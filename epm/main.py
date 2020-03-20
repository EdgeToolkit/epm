import sys

from epm.command import main

#############################
import inspect
import json
import os
import sys
import errno
import argparse
from argparse import ArgumentError
from difflib import get_close_matches


from conans.client.cmd.uploader import UPLOAD_POLICY_FORCE, \
    UPLOAD_POLICY_NO_OVERWRITE, UPLOAD_POLICY_NO_OVERWRITE_RECIPE, UPLOAD_POLICY_SKIP
from conans.client.conan_api import (Conan, default_manifest_folder, _make_abs_path)
from conans.client.conan_command_output import CommandOutputer
from conans.client.output import Color, ConanOutput

from conans.unicode import get_cwd
from conans.util.files import exception_message_safe

from epm import __version__
from epm.errors import EException, ECommandError, EInvalidConfiguration
from epm.api import API
from epm.util.files import load_yaml
from epm.worker import param_decode

from epm import commands

# Exit codes for conan command:
SUCCESS = 0                         # 0: Success (done)
ERROR_GENERAL = 1                   # 1: General ConanException error (done)
ERROR_MIGRATION = 2                 # 2: Migration error
USER_CTRL_C = 3                     # 3: Ctrl+C
USER_CTRL_BREAK = 4                 # 4: Ctrl+Break
ERROR_SIGTERM = 5                   # 5: SIGTERM
ERROR_INVALID_CONFIGURATION = 6     # 6: Invalid configuration (done)

_DESCRIPTION = 'Embedded-system package manager for C/C++ development base on conan.'
_PROFILE_HELP = 'Profile of the target package, this required in build/create/sandbox/upload command'
_SCHEME_HELP = 'Scheme of the target package'
_RUNNER_HELP = 'Runner of the command used to execute/process'

class Main(object):

    def __init__(self, args, api=None):
        self._api = api or API()
        self._out = self._api.out or ConanOutput(sys.stdout)
#        if user_is_root():
#            m.warning(_("Running as root"))

#        self.check_in_cerbero_shell()
        self.create_parser()
        self.load_commands()
        self.parse_arguments(args)
#        self.self_update()
#        self.init_logging()
#        self.load_config()
#        self.list_variants()
        self.run_command()

#    def check_in_cerbero_shell(self):
#        if os.environ.get('CERBERO_PREFIX', '') != '':
#            self.log_error(_("ERROR: cerbero can't be run "
#                             "from a cerbero shell"))
#
#    def log_error(self, msg, print_usage=False, command=None):
#        ''' Log an error and exit '''
#        if command is not None:
#            m.error("***** Error running '%s' command:" % command)
#        m.error('%s' % msg)
#        if print_usage:
#            self.parser.print_usage()
#        sys.exit(1)
#
#    def init_logging(self):
#        ''' Initialize logging '''
#        if self.args.timestamps:
#            m.START_TIME = time.monotonic()
#        logging.getLogger().setLevel(logging.INFO)
#        logging.getLogger().addHandler(logging.StreamHandler())

    def create_parser(self):
        ''' Creates the arguments parser '''

        self.parser = argparse.ArgumentParser(description=_DESCRIPTION,
                                              formatter_class=commands.SmartFormatter)

        self.parser.add_argument('-p', '--profile', dest='PROFILE', type=str, default=None, help=_PROFILE_HELP)
        self.parser.add_argument('-s', '--scheme', dest='SCHEME', type=str, default=None, help=_SCHEME_HELP)
        self.parser.add_argument('-r', '--runner', dest='RUNNER', type=str, default=None, help=_RUNNER_HELP)

    def parse_arguments(self, args):
        ''' Parse the command line arguments '''
        # If no commands, make it show the help by default
        if len(args) == 0:
            args = ["-h"]
        self.args = self.parser.parse_args(args)

#    def list_variants(self):
#        if not self.args.list_variants:
#            return
#        print('Available variants are: ' + ', '.join(self.config.variants.all()))
#        sys.exit(0)

    def load_commands(self):
        subparsers = self.parser.add_subparsers(help='sub-command help',
                                                dest='command')
        commands.load_commands(subparsers)

#    def load_config(self):
#        ''' Load the configuration '''
#        try:
#            self.config = config.Config()
#            if self.args.command == 'shell':
#                self.config.for_shell = True
#            self.config.load(self.args.config, self.args.variants)
#            if self.args.manifest:
#                self.config.manifest = self.args.manifest
#        except ConfigurationError as exc:
#            self.log_error(exc, False)

    def run_command(self):
        command = self.args.command
        try:
            res = commands.run(command, self.config, self.args)
#        except UsageError as exc:
#            self.log_error(exc, True, command)
#            sys.exit(1)
#        except FatalError as exc:
#            traceback.print_exc()
#            self.log_error(exc, True, command)
#        except BuildStepError as exc:
#            self.log_error(exc.msg, False, command)
#        except AbortedError as exc:
#            self.log_error('', False, command)
#        except CerberoException as exc:
#            self.log_error(exc, False, command)
        except SystemExit as exc:
            if exc.code != 0:
                self._out.error("Exiting with code: %d" % exc.code)
            res = exc.code

        except KeyboardInterrupt:
            self._out.error('Interrupted')
        except IOError as e:
            if e.errno != errno.EPIPE:
                raise
            sys.exit(0)

        if res:
            sys.exit(res)


def run():
    #main(sys.argv[1:])
    Main(sys.argv[1:])


if __name__ == '__main__':
    run()
