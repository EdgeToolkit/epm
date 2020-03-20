
from epm.commands import Command, register_command, ArgparseArgument


class Upload(Command):
    """
    Builds a binary package and storage in local cache.

    Uses the specified PROFILE and SCHEME.
    """

    name = 'upload'
    help = 'Uploads created package to remote.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [
                ArgparseArgument("-r", "--remote", default=None,
                                    help="the remote where upload to, if not specified,"
                                         "upload to `group` defined in package.yml"),
                ArgparseArgument("--storage", default=None,
                                    help="upload the local conan cache "),

                ]
            Command.__init__(self, args)

    def run(self, config, args):
        print('YES')


register_command(Upload)
