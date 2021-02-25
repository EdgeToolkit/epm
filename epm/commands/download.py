
from epm.commands import Command, register_command, ArgparseArgument


class Download(Command):
    """
    """

    name = 'download'
    help = 'Dowload package according reference or conaninfo.txt deps.'
    prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
            args = [
                ArgparseArgument("-r", "--remote", default=None, action="append",
                                    help="the remote where package download from."),

#                ArgparseArgument("--storage", default=None,
#                                    help="upload the local conan cache "),

                ArgparseArgument("--reference", default=None, help=""),

                ArgparseArgument("--exclude", default=list(), action="append", help=""),

            ]
            Command.__init__(self, args)

    def run(self, args, api):
        param = self.parameter(args)

        param['remote'] = args.remote
#        param['storage'] = args.storage
        param['reference'] = args.reference
        param['exclude'] = args.exclude

        api.download(param)


register_command(Download)
