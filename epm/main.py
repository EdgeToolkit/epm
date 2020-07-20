import sys
import json
import os
import time
import errno
import argparse
import traceback

from conans.client.output import Color, colorama_initialize
from epm import commands
from epm.model.runner import Output
from epm.errors import EException

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

    def __init__(self, args, out=None):
        color = colorama_initialize()
        self.out = out or Output(sys.stdout, sys.stderr, color)
        self.create_parser()
        self.load_commands()
        self.parse_arguments(args)
        self.run_command()

    def create_parser(self):
        ''' Creates the arguments parser '''

        self.parser = argparse.ArgumentParser(description=_DESCRIPTION,
                                              formatter_class=commands.SmartFormatter)
        self.parser.add_argument('-v', '--version', dest='_VERSION', default=False, action="store_true", help="show version of epm.")

        self.parser.add_argument('-p', '--profile', dest='PROFILE', type=str, default=None, help=_PROFILE_HELP)
        self.parser.add_argument('-s', '--scheme', dest='SCHEME', type=str, default=None, help=_SCHEME_HELP)
        self.parser.add_argument('-r', '--runner', dest='RUNNER', type=str, default=None, help=_RUNNER_HELP)

    def parse_arguments(self, args):
        ''' Parse the command line arguments '''
        # If no commands, make it show the help by default
        if len(args) == 0:
            args = ["-h"]

        known, unkown = self.parser.parse_known_args(args)
        command = known.command
        if command in ['sandbox', 'run']:
            self.args = known
            self.args.argv = unkown
        else:
            self.args = self.parser.parse_args(args)

    def load_commands(self):
        subparsers = self.parser.add_subparsers(help='sub-command help',
                                                dest='command')
        commands.load_commands(subparsers)

    def run_command(self):
        command = self.args.command
        res = 255
        try:
            res = commands.run(command, self.args, self.out)
        except SystemExit as exc:
            if exc.code != 0:
                self.out.error("Exiting with code: %d" % exc.code)
            res = exc.code

        except KeyboardInterrupt:
            self.out.error('Interrupted')
        except IOError as e:
            if e.errno != errno.EPIPE:
                raise
        except Exception as e:
            res = self._error(e)

        if res:
            sys.exit(res)

    def _error(self, e):
        from epm import __version__ as version

        #if not os.path.exists('.epm'):
        #    os.makedirs('.epm')
        #
        #tb = traceback.format_exc()
        #msg = str(e)
        #is_docker = False

        if isinstance(e, EException):
            self.out.error(e.message)
            e.traceback('.epm/traceback.log')
        else:
            print('------------------------')
            print(type(e), str(e))
            import traceback
            traceback.print_tb(e.__traceback__)


        #if self.args.command == 'api':
        #
        #    info = {'msg': msg,
        #            'version': version,
        #            'command': self.args.command,
        #            'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        #            'traceback': tb
        #            }
        #    with open('.epm/errors.json', 'w') as f:
        #        json.dump(info, f)
        #else:
        #    hint = ' docker epm %s ' % version if is_docker else ''
        #    hint = '{:=^80s}'.format(hint)
        #
        #    self.out.write('\n{}\n'.format(hint))
        #    self.out.error(msg)
        #    with open('.epm/traceback.log', 'w') as f:
        #        f.write(str(tb))

        return 1



def run():
    Main(sys.argv[1:])


if __name__ == '__main__':
    run()
