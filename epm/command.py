import inspect
import json
import os
import sys

import argparse
from argparse import ArgumentError
from difflib import get_close_matches


from conans.client.cmd.uploader import UPLOAD_POLICY_FORCE, \
    UPLOAD_POLICY_NO_OVERWRITE, UPLOAD_POLICY_NO_OVERWRITE_RECIPE, UPLOAD_POLICY_SKIP
from conans.client.conan_api import (Conan, default_manifest_folder, _make_abs_path)
from conans.client.conan_command_output import CommandOutputer
from conans.client.output import Color

from conans.unicode import get_cwd
from conans.util.files import exception_message_safe

from epm import __version__
from epm.errors import EException, ECommandError, EInvalidConfiguration
from epm.api import API
from epm.util.files import load_yaml


# Exit codes for conan command:
SUCCESS = 0                         # 0: Success (done)
ERROR_GENERAL = 1                   # 1: General ConanException error (done)
ERROR_MIGRATION = 2                 # 2: Migration error
USER_CTRL_C = 3                     # 3: Ctrl+C
USER_CTRL_BREAK = 4                 # 4: Ctrl+Break
ERROR_SIGTERM = 5                   # 5: SIGTERM
ERROR_INVALID_CONFIGURATION = 6     # 6: Invalid configuration (done)


class Extender(argparse.Action):
    """Allows to use the same flag several times in a command and creates a list with the values.
    For example:
        conan install MyPackage/1.2@user/channel -o qt:value -o mode:2 -s cucumber:true
      It creates:
          options = ['qt:value', 'mode:2']
          settings = ['cucumber:true']
    """
    def __call__(self, parser, namespace, values, option_strings=None):  # @UnusedVariable
        # Need None here incase `argparse.SUPPRESS` was supplied for `dest`
        dest = getattr(namespace, self.dest, None)
        if not hasattr(dest, 'extend') or dest == self.default:
            dest = []
            setattr(namespace, self.dest, dest)
            # if default isn't set to None, this method might be called
            # with the default as `values` for other arguments which
            # share this destination.
            parser.set_defaults(**{self.dest: None})

        if isinstance(values, str):
            dest.append(values)
        elif values:
            try:
                dest.extend(values)
            except ValueError:
                dest.append(values)


class OnceArgument(argparse.Action):
    """Allows to declare a parameter that can have only one value, by default argparse takes the
    latest declared and it's very confusing.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is not None and self.default is None:
            msg = '{o} can only be specified once'.format(o=option_string)
            raise argparse.ArgumentError(None, msg)
        setattr(namespace, self.dest, values)


class SmartFormatter(argparse.HelpFormatter):

    def _fill_text(self, text, width, indent):
        import textwrap
        text = textwrap.dedent(text)
        return ''.join(indent + line for line in text.splitlines(True))


_QUERY_EXAMPLE = "os=Windows AND (arch=x86 OR compiler=gcc)"
_PATTERN_EXAMPLE = "boost/*"
_REFERENCE_EXAMPLE = "MyPackage/1.2@user/channel"
_PREF_EXAMPLE = "MyPackage/1.2@user/channel:af7901d8bdfde621d086181aa1c495c25a17b137"

_BUILD_FOLDER_HELP = ("Directory for the build process. Defaulted to the current directory. A "
                      "relative path to current directory can also be specified")
_INSTALL_FOLDER_HELP = ("Directory containing the conaninfo.txt and conanbuildinfo.txt files "
                        "(from previous 'conan install'). Defaulted to --build-folder")
_KEEP_SOURCE_HELP = ("Do not remove the source folder in local cache, even if the recipe changed. "
                     "Use this for testing purposes only")
_PATTERN_OR_REFERENCE_HELP = ("Pattern or package recipe reference, e.g., '%s', "
                              "'%s'" % (_PATTERN_EXAMPLE, _REFERENCE_EXAMPLE))
_PATTERN_REF_OR_PREF_HELP = ("Pattern, recipe reference or package reference e.g., '%s', "
                             "'%s', '%s'" % (_PATTERN_EXAMPLE, _REFERENCE_EXAMPLE, _PREF_EXAMPLE))
_REF_OR_PREF_HELP = ("Recipe reference or package reference e.g., '%s', "
                     "'%s'" % (_REFERENCE_EXAMPLE, _PREF_EXAMPLE))
_PATH_HELP = ("Path to a folder containing a conanfile.py or to a recipe file "
              "e.g., my_folder/conanfile.py")
_QUERY_HELP = ("Packages query: '%s'. The 'pattern_or_reference' parameter has "
               "to be a reference: %s" % (_QUERY_EXAMPLE, _REFERENCE_EXAMPLE))
_SOURCE_FOLDER_HELP = ("Directory containing the sources. Defaulted to the conanfile's directory. A"
                       " relative path to current directory can also be specified")


class Command(object):
    """A single command of the conan application, with all the first level commands. Manages the
    parsing of parameters and delegates functionality in collaborators. It can also show help of the
    tool.
    """
    def __init__(self, api):
        assert isinstance(api, API)
        self._api = api
        self._out = api.out

    @property
    def _outputer(self):
        # FIXME, this access to the cache for output is ugly, should be removed
        return CommandOutputer(self._out, self._conan.app.cache)

    def _argument_parser(self, name):
        parser = argparse.ArgumentParser(description=getattr(self, name).__doc__,
                                         prog="epm %s" % name,
                                         formatter_class=SmartFormatter)
        return parser

    def help(self, *args):
        """
        Shows help for a specific command.
        """
        parser = argparse.ArgumentParser(description=self.help.__doc__,
                                         prog="epm help",
                                         formatter_class=SmartFormatter)
        parser.add_argument("command", help='command', nargs="?")
        args = parser.parse_args(*args)
        if not args.command:
            self._show_help()
            return
        try:
            commands = self._commands()
            method = commands[args.command]
            self._warn_python_version()
            method(["--help"])
        except KeyError:
            raise EException("Unknown command '%s'" % args.command)

    def api(self, *args):
        """
        Call epm api with command line.

        API param is json with base64 encode pass to command.
        """
        parser = self._argument_parser('api')
        parser.add_argument('method', nargs=1, help=_APICALL_METHOD)
        parser.add_argument('param', nargs='?', help=_APICALL_PARAM)

        args = parser.parse_args(*args)
        param = None
        if args.param:
            param = param_decode(args.param)

        method = getattr(self._api, args.method[0])
        if not method:
            raise EException('epm api no method <%s>' % args.method)
        method(param)


    def create(self, *args):
        """
        Builds a binary package for a recipe (conanfile.py).

        Uses the specified configuration in a profile or in -s settings, -o
        options etc. If a 'test_package' folder (the name can be configured
        with -tf) is found, the command will run the consumer project to ensure
        that the package has been created correctly. Check 'conan test' command
        to know more about 'test_folder' project.
        """
        parser = argparse.ArgumentParser(description=self.create.__doc__,
                                         prog="epm create",
                                         formatter_class=SmartFormatter)

        parser.add_argument("-s", "--scheme", type=str,
                            help="the plan to build for, etc vs2019, gcc5@dynmic ....")

        parser.add_argument("-r", "--runner", default=None, type=str,
                            help="specified the runner (auto, shell, docker) to execute the command, default is 'auto'")

        parser.add_argument("--storage", default=None,
                            help="all conan package will be download and cached under project directory"
                            "that is conan storage path will be set at .conan folder in project.")

        parser.add_argument("--clear", default=False, action="store_true",
                            help="clear local cache of .conan in project")

        args = parser.parse_args(*args)

        result = self._api.create({'scheme': args.scheme,
                                   'storage': args.storage,
                                   'clear': args.clear})

#        def _size(n):
#            for uint in ['', 'K', 'M']:
#                if n/1000.0 < 1.0:
#                    break
#                n /= 1000
#            return n, uint
#
#        for i, name in [('.epm', '.epm'), ('$storage', 'storage')]:
#            size = result.get('dirs', {}).get(i, {}).get('size')
#            if size:
#                print(name, '%d %s' % _size(size))

    def build(self, *args):
        """
        Builds the local package.

        """

        parser = argparse.ArgumentParser(description=self.build.__doc__,
                                         prog="epm build",
                                         formatter_class=SmartFormatter)

        parser.add_argument("-s", "--scheme", type=str,
                            help="the plan to build for, etc vs2019, gcc5@dynmic ....")

        parser.add_argument("-r", "--runner", default=None, type=str,
                            help="specified the runner (auto, shell, docker) to execute the command, default is 'auto'")

        parser.add_argument("-c", "--configure", default=None, action="store_true",
                            help="Execute the configuration step to configure the this C/C++ project. "
                            "When specified, build/install/test won't run unless "
                            "--build/--install/--test specified")

        parser.add_argument("-p", "--package", default=None, action="store_true",
                            help="Execute the package build step to make the C/C++ lib or program,. When "
                            "specified, configure/install/test won't run unless "
                            "--configure/--install/--test specified")

        parser.add_argument("-i", "--install", default=None, action="store_true",
                            help="Execute the package install step to install the built package to package folder. When"
                            "specified, configure/package/test won't run unless "
                            "--configure/--package/--test specified")

        parser.add_argument("-t", "--test", default=None, action="store_true",
                            help="Execute the test_package build step. When "
                            "specified, configure/package/install won't run unless "
                            "--configure/--package/--install specified")

        args = parser.parse_args(*args)

#        self._warn_python_version()

        if args.package or args.configure or args.install or args.test:
            package, configure, install, test = \
                (bool(args.package), bool(args.configure), bool(args.install), bool(args.test))
        else:
            package = configure = install = test = True

        steps = ['configure'] if configure else []
        steps += ['package'] if package else []
        steps += ['install'] if install else []
        steps += ['test'] if test else []
        param = {'runner': args.runner,
                 'scheme': args.scheme,
                 'step': steps}
        self._api.build(param)
        return

        from epm.model.project import Project
        project = Project(args.scheme, self._api)
        profile = project.scheme.profile

        runner = args.runner or 'auto'
        if runner == ['auto']:
            if profile.builders:
                runner = profile.builders[0]
            else:
                raise EException('Not found proper builder according the --runner options %s' % args.runner)

        if runner == 'shell':
            self._api.build(param)
        elif runner == 'docker':
            from epm.tool.docker import Docker
            debug = self._debug
            config = profile.docker.builder

            if debug:
                image = debug.get('images', {}).get(config['image']).get('image')
                if image:
                    config['image'] = image

            docker = Docker(profile.docker.builder)
            docker.volume = {
                '$home/host/.epm': {'source': self._api.cache_folder},
                '$home/project/{}'.format(project.name): {'source': project.dir}
            }

            if debug:
                install = debug.get('images', {}).get(config['image']).get('install')
                if install:
                    docker.volume[install]


            # mount $CD => $docker.home/host/$(project.name)
            # ~/.epm    => $docker.home/host/.epm

            docker = Docker()
            docker.volume.append({'type':'bind', 'source': os.path.abspath('.'), 'target': '$home/'})
            pass
        else:
            print('remote build not support !!!')



    def upload(self, *args):
        """
        Uploads a recipe and binary packages to a remote.

        If no remote is specified, the first configured remote (by default conan-center, use
        'conan remote list' to list the remotes) will be used.
        """
        parser = argparse.ArgumentParser(description=self.upload.__doc__,
                                         prog="conan upload",
                                         formatter_class=SmartFormatter)
        parser.add_argument('pattern_or_reference', help=_PATTERN_REF_OR_PREF_HELP)
        parser.add_argument("-p", "--package", default=None,
                            help="Package ID [DEPRECATED: use full reference instead]",
                            action=OnceArgument)
        parser.add_argument('-q', '--query', default=None, action=OnceArgument,
                            help="Only upload packages matching a specific query. " + _QUERY_HELP)
        parser.add_argument("-r", "--remote", action=OnceArgument,
                            help='upload to this specific remote')
        parser.add_argument("--all", action='store_true', default=False,
                            help='Upload both package recipe and packages')
        parser.add_argument("--skip-upload", action='store_true', default=False,
                            help='Do not upload anything, just run the checks and the compression')
        parser.add_argument("--force", action='store_true', default=False,
                            help='Do not check conan recipe date, override remote with local')
        parser.add_argument("--check", action='store_true', default=False,
                            help='Perform an integrity check, using the manifests, before upload')
        parser.add_argument('-c', '--confirm', default=False, action='store_true',
                            help='Upload all matching recipes without confirmation')
        parser.add_argument('--retry', default=None, type=int, action=OnceArgument,
                            help="In case of fail retries to upload again the specified times.")
        parser.add_argument('--retry-wait', default=None, type=int, action=OnceArgument,
                            help='Waits specified seconds before retry again')
        parser.add_argument("-no", "--no-overwrite", nargs="?", type=str, choices=["all", "recipe"],
                            action=OnceArgument, const="all",
                            help="Uploads package only if recipe is the same as the remote one")
        parser.add_argument("-j", "--json", default=None, action=OnceArgument,
                            help='json file path where the upload information will be written to')
        parser.add_argument("--parallel", action='store_true', default=False,
                            help='Upload files in parallel using multiple threads '
                                 'The default number of launched threads is 8')

        args = parser.parse_args(*args)

        try:
            pref = PackageReference.loads(args.pattern_or_reference, validate=True)
        except ConanException:
            reference = args.pattern_or_reference
            package_id = args.package

            if package_id:
                self._out.warn("Usage of `--package` argument is deprecated."
                               " Use a full reference instead: "
                               "`conan upload [...] {}:{}`".format(reference, package_id))

            if args.query and package_id:
                raise ConanException("'--query' argument cannot be used together with '--package'")
        else:
            reference = repr(pref.ref)
            package_id = "{}#{}".format(pref.id, pref.revision) if pref.revision else pref.id

            if args.package:
                raise ConanException("Use a full package reference (preferred) or the `--package`"
                                     " command argument, but not both.")
            if args.query:
                raise ConanException("'--query' argument cannot be used together with "
                                     "full reference")

        if args.force and args.no_overwrite:
            raise ConanException("'--no-overwrite' argument cannot be used together with '--force'")
        if args.force and args.skip_upload:
            raise ConanException("'--skip-upload' argument cannot be used together with '--force'")
        if args.no_overwrite and args.skip_upload:
            raise ConanException("'--skip-upload' argument cannot be used together "
                                 "with '--no-overwrite'")

        self._warn_python_version()

        if args.force:
            policy = UPLOAD_POLICY_FORCE
        elif args.no_overwrite == "all":
            policy = UPLOAD_POLICY_NO_OVERWRITE
        elif args.no_overwrite == "recipe":
            policy = UPLOAD_POLICY_NO_OVERWRITE_RECIPE
        elif args.skip_upload:
            policy = UPLOAD_POLICY_SKIP
        else:
            policy = None

        info = None
        try:
            info = self._conan.upload(pattern=reference, package=package_id,
                                      query=args.query, remote_name=args.remote,
                                      all_packages=args.all, policy=policy,
                                      confirm=args.confirm, retry=args.retry,
                                      retry_wait=args.retry_wait, integrity_check=args.check,
                                      parallel_upload=args.parallel)

        except ConanException as exc:
            info = exc.info
            raise
        finally:
            if args.json and info:
                self._outputer.json_output(info, args.json, os.getcwd())

    def init(self, *args):
        """
        Initialize project

        """
        parser = argparse.ArgumentParser(description=self.init.__doc__,
                                         prog="epm init",
                                         formatter_class=SmartFormatter)

        subparsers = parser.add_subparsers(help='@@@', dest='command')

        def _common_args(sp):


            sp.add_argument('--name', default=None,
                            help="name of package. if not specified,"
                                 "use the `name` in package.yml. if the package.yml not exists or no `name` field"
                                 "use folder name as project name"),

            sp.add_argument('--version', default=None,
                            help="version of package. if not specified,use the field of `version` in package.yml."
                                 "if the package.yml not exists or no name field defined in it"
                                 "use 0.0.1 as first package version.")

        lib = subparsers.add_parser("lib")
        _common_args(lib)

        app = subparsers.add_parser("app")
        _common_args(app)
        args = parser.parse_args(*args)
        print(args)

#        if args not in ['app', 'lib']:
#            raise EException('Unsupported package type %s' % args.command)
        from epm.tool.project import Generator
        gen = Generator(args, args.command)
        return gen.run()

    def sandbox(self, *args):
        """
        epm sandbox --scheme gcc5 --runner docker <command> options...

        The --scheme and --runner options of sandbox must placed before <command>,
        otherwise it will be token as the sandbox <command> options
        """
        parser = self._argument_parser('sandbox')

        parser.add_argument("-s", "--scheme", type=str,
                            help="scheme of the sandbox, etc vs2019, gcc5@dynmic ....")

        parser.add_argument("-r", "--runner", default=None, type=str,
                            help="specified the runner (auto, shell, docker) to execute the command, default is 'auto'")

        parser.add_argument("command", nargs=1)
        known, unkown = parser.parse_known_args(*args)
        argv = args[0]

        # located the command
        command = known.command[0]

        # check if command is defined in package.yml
        manifest = load_yaml('package.yml')
        commands = manifest.get('sandbox', {})
        if command not in commands:
            raise ECommandError('Invalid sandbox command <%s>' % command)

        pos = argv.index(command)
        args = parser.parse_args(argv[:pos+1])

        param = {'runner': args.runner,
                 'scheme': args.scheme,
                 'command': command,
                 'args': argv[pos+1:]}

        result = self._api.sandbox(param)
        if result:
            raise EException('sandbox %s executed, exit code %d' % (command, result))

    def _show_help(self):
        """
        Prints a summary of all commands.
        """
        grps = [#("Consumer commands", ("config", )),
                ("Creator commands", ("init", "create", "upload")),
                ("Package development commands", ("build", "sandbox")),
                ("Misc commands", ("help", "api"))]

        def check_all_commands_listed():
            """Keep updated the main directory, raise if don't"""
            all_commands = self._commands()
            all_in_grps = [command for _, command_list in grps for command in command_list]
            if set(all_in_grps) != set(all_commands):
                diff = set(all_commands) - set(all_in_grps)
                raise Exception("Some command is missing in the main help: %s" % ",".join(diff))
            return all_commands

        commands = check_all_commands_listed()
        max_len = max((len(c) for c in commands)) + 1
        fmt = '  %-{}s'.format(max_len)

        for group_name, comm_names in grps:
            self._out.writeln(group_name, Color.BRIGHT_MAGENTA)
            for name in comm_names:
                # future-proof way to ensure tabular formatting
                self._out.write(fmt % name, Color.GREEN)

                # Help will be all the lines up to the first empty one
                docstring_lines = commands[name].__doc__.split('\n')
                start = False
                data = []
                for line in docstring_lines:
                    line = line.strip()
                    if not line:
                        if start:
                            break
                        start = True
                        continue
                    data.append(line)

                import textwrap
                txt = textwrap.fill(' '.join(data), 80, subsequent_indent=" "*(max_len+2))
                self._out.writeln(txt)

        self._out.writeln("")
        self._out.writeln('EPM commands. Type "epm <command> -h" for help', Color.BRIGHT_YELLOW)

    def _commands(self):
        """ returns a list of available commands
        """
        result = {}
        for m in inspect.getmembers(self, predicate=inspect.ismethod):
            method_name = m[0]
            if not method_name.startswith('_'):

                method = m[1]
                if method.__doc__ and not method.__doc__.startswith('HIDDEN'):
                    result[method_name] = method
        return result

    def _print_similar(self, command):
        """ looks for a similar commands and prints them if found
        """
        matches = get_close_matches(
            word=command, possibilities=self._commands().keys(), n=5, cutoff=0.75)

        if len(matches) == 0:
            return

        if len(matches) > 1:
            self._out.writeln("The most similar commands are")
        else:
            self._out.writeln("The most similar command is")

        for match in matches:
            self._out.writeln("    %s" % match)

        self._out.writeln("")

    def _warn_python_version(self):
        version = sys.version_info
        if version.major == 2:
            self._out.writeln("*"*70, front=Color.BRIGHT_RED)
            self._out.writeln("Python 2 will soon be deprecated. It is strongly "
                              "recommended to use Python >= 3.5 with Conan:",
                              front=Color.BRIGHT_RED)
            self._out.writeln("https://docs.conan.io/en/latest/installation.html"
                              "#python-2-deprecation-notice", front=Color.BRIGHT_RED)
            self._out.writeln("*"*70, front=Color.BRIGHT_RED)
        elif version.minor == 4:
            self._out.writeln("*"*70, front=Color.BRIGHT_RED)
            self._out.writeln("Python 3.4 support has been dropped. It is strongly "
                              "recommended to use Python >= 3.5 with Conan",
                              front=Color.BRIGHT_RED)
            self._out.writeln("*"*70, front=Color.BRIGHT_RED)

    def run(self, *args):
        """HIDDEN: entry point for executing commands, dispatcher to class
        methods
        """
        ret_code = SUCCESS
        try:
            try:
                command = args[0][0]
            except IndexError:  # No parameters
                self._show_help()
                return False
            try:
                commands = self._commands()
                method = commands[command]
            except KeyError as exc:
                if command in ["-v", "--version"]:
                    self._out.success("EPM version %s" % __version__)
                    return False

                self._warn_python_version()

                if command in ["-h", "--help"]:
                    self._show_help()
                    return False

                self._out.writeln(
                    "'%s' is not a EPM command. See 'epm --help'." % command)
                self._out.writeln("")
                self._print_similar(command)
                raise EException("Unknown command %s" % str(exc))

            method(args[0][1:])
        except KeyboardInterrupt as exc:
            #logger.error(exc)
            ret_code = SUCCESS
        except SystemExit as exc:
            if exc.code != 0:
               # logger.error(exc)
                self._out.error("Exiting with code: %d" % exc.code)
            ret_code = exc.code
        except EInvalidConfiguration as exc:
            ret_code = ERROR_INVALID_CONFIGURATION
            self._out.error(exc)
        except EException as exc:
            ret_code = ERROR_GENERAL
            self._out.error(exc)
        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            ret_code = ERROR_GENERAL
            msg = exception_message_safe(exc)
            self._out.error(msg)

        return ret_code


def main(args):
    """ main entry point of the conan application, using a Command to
    parse parameters

    Exit codes for epm command:

        0: Success (done)
        1: General error (done)
        2: Migration error
        3: Ctrl+C
        4: Ctrl+Break
        5: SIGTERM
        6: Invalid configuration (done)
    """
    try:
        api = API()
#    except ConanMigrationError:  # Error migrating
#        sys.exit(ERROR_MIGRATION)
    except EException as e:
        sys.stderr.write("Error in Conan initialization: {}".format(e))
        sys.exit(ERROR_GENERAL)

    command = Command(api)
    current_dir = get_cwd()
    try:
        import signal

        def ctrl_c_handler(_, __):
            print('You pressed Ctrl+C!')
            sys.exit(USER_CTRL_C)

        def sigterm_handler(_, __):
            print('Received SIGTERM!')
            sys.exit(ERROR_SIGTERM)

        def ctrl_break_handler(_, __):
            print('You pressed Ctrl+Break!')
            sys.exit(USER_CTRL_BREAK)

        signal.signal(signal.SIGINT, ctrl_c_handler)
        signal.signal(signal.SIGTERM, sigterm_handler)

        if sys.platform == 'win32':
            signal.signal(signal.SIGBREAK, ctrl_break_handler)
        error = command.run(args)
    finally:
        os.chdir(current_dir)
    sys.exit(error)


_APICALL_METHOD = "the api method to be called"

_APICALL_PARAM = "param of api method which is base64 encode for json"

from epm.worker import param_decode

def api_main(argv):
    parser = argparse.ArgumentParser(description="epm api invoke command",
                                     prog="epm.api.call")

    parser.add_argument('method', nargs=1, help=_APICALL_METHOD)
    parser.add_argument('param', nargs='?', help=_APICALL_PARAM)

    args = parser.parse_args(argv)
    param = None
    if args.param:
        param = param_decode(args.param)
    print('----------------api_main------------------------')
    print(param)
