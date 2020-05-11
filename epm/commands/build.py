
from epm.commands import Command, register_command, ArgparseArgument


class Build(Command):
    '''
    Build specified target package according PROFILE and SCHEME.
    if the SCHEME not specified, will build default options (which defined
    in conanfile.py default_options).

    The RUNNER can be auto, shell, docker. if not specified, it will take as auto.

    '''

    name = 'build'
    help = 'Builds a binary package for the project.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [

                ArgparseArgument("-c", "--configure", default=None, action="store_true",
                                    help="Execute the configuration step to configure the this C/C++ project."
                                         "When specified, make/package/sandbox won't run unless "
                                         "--make/--package/--sandbox specified"),

                ArgparseArgument("-m", "--make", default=None, action="store_true",
                                    help="Execute the make step to build the C/C++ lib or executable,. When "
                                         "specified, configure/package/sandbox won't run unless "
                                         "--configure/--package/--sandbox specified"),

                ArgparseArgument("-p", "--package", default=None, action="store_true",
                                    help="Execute the package step to archive the project to package folder. When"
                                         "specified, configure/make/sandbox won't run unless "
                                         "--configure/--make/--sandbox specified"),

                ArgparseArgument("-s", "--sandbox", default=None, type=str,
                                 help="Execute sandbox program build. when sepcified,"
                                      "configure/make/package won't runless"
                                      "--configure/--make/package specified."
                                      "If not set, all sandbox will be built after configure/make/package"
                                      "If set, only build specified sandbox program, or '*' for all sandbox program")
                ]
            Command.__init__(self, args)

    def run(self, args, api):
        steps = []
        steps += ['configure'] if args.configure else []
        steps += ['make'] if args.make else []
        steps += ['package'] if args.package else []
        param = self.parameter(args)
        param['steps'] = steps
        param['sandbox'] = args.sandbox

        api.build(param)



class SandboxBuild(Command):
    '''
    Build Sandbox program specified target package according PROFILE and SCHEME.
    if the SCHEME not specified, will build default options (which defined
    in conanfile.py default_options).

    The RUNNER can be auto, shell, docker. if not specified, it will take as auto.

    '''

    name = 'sandbox-build'
    help = 'Build sandbox program with cached reference.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [
                ArgparseArgument("name", nargs='*', default=None,
                                 help="name of the sandbox to be built"),

                ArgparseArgument("-c", "--configure", default=None, action="store_true",
                                    help="Execute the configuration step to configure the this C/C++ project. "
                                         "When specified, build/install/test won't run unless "
                                         "--make/--package/--test specified"),

                ArgparseArgument("-m", "--make", default=None, action="store_true",
                                    help="Execute the make step to build the C/C++ lib or executable,. When "
                                         "specified, configure/install/test won't run unless "
                                         "--configure/--package/--test specified")


                ]
            Command.__init__(self, args)

    def run(self, args, api):
        print('----------------------------------------')
        print(args)
        print('----------------------------------------')
        steps = []
        steps += ['configure'] if args.configure else []
        steps += ['make'] if args.make else []
        param = self.parameter(args)
        param['steps'] = steps
        param['name'] = args.name or None
        print('----------------------------------------')
        print(param)
        print('----------------------------------------')

        api.sandbox_build(param)


register_command(Build)
register_command(SandboxBuild)
