
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
                                    help="Execute the configuration step to configure the this C/C++ project. "
                                         "When specified, build/install/test won't run unless "
                                         "--make/--package/--test specified"),

                ArgparseArgument("-m", "--make", default=None, action="store_true",
                                    help="Execute the make step to build the C/C++ lib or executable,. When "
                                         "specified, configure/install/test won't run unless "
                                         "--configure/--package/--test specified"),

                ArgparseArgument("-p", "--package", default=None, action="store_true",
                                    help="Execute the package step to archive the project to package folder. When"
                                         "specified, configure/make/test won't run unless "
                                         "--configure/--make/--test specified"),

                ArgparseArgument("-t", "--test", default=None, action="store_true",
                                    help="Execute the package test build step when `test_package` exists. When "
                                         "specified, configure/package/install won't run unless "
                                         "--configure/--package/--install specified")


                ]
            Command.__init__(self, args)

    def run(self, config, args):
        print('YES')


register_command(Build)
