
from epm.commands import Command, register_command, ArgparseArgument


class Download(Command):
    '''
    Build specified target package according PROFILE and SCHEME.
    if the SCHEME not specified, will build default options (which defined
    in conanfile.py default_options).

    The RUNNER can be auto, shell, docker. if not specified, it will take as auto.

    '''

    name = 'download'
    help = 'Builds a binary package for the project.'
    prog = 'epm [-p PROFILE] [-s SCHEME] %s' % name

    def __init__(self):
            args = [
                ArgparseArgument("reference", nargs='+', type=str,  help="package reference to download."),

                ArgparseArgument("-d", "--directory", default='.',  help="directory to be store"),
                ArgparseArgument("-c", "--cache", default=None, help="cache directory"),

            ]
            Command.__init__(self, args)

    def run(self, args, api):

        param = self.parameter(args)
        param.update({
            'reference': args.reference,
            'directory': args.directory,
            'cache': args.cache
        })
        print(param)

        api.download(param)



register_command(Download)

