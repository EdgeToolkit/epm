
from epm.commands import Command, register_command, ArgparseArgument

_install_args = [

    ArgparseArgument("location", type=str,
                     help="location of the install source, support local directory or http/hppts zip url."),

    ArgparseArgument("--install-dir", type=str, default=None,
                     help="where to installed, by default it will be installed on ~/.epm/venv/{name}"),
]

_active_args = [
    ArgparseArgument("name", default=None, type=str,
                     help="The name of install virtual environment."),
]

_list_args = [
    ArgparseArgument("name", default=None, type=str,
                     help="If the name not specified, all installed will be shown."),
]

_banner_args = [
    ArgparseArgument("name", nargs='?', default=None, type=str,
                     help="The name venv."),
]

_uninstall_args = [
    ArgparseArgument("name", default=None, type=str,
                     help="The name to be uninstalled."),
]

# epm venv install url --install-dir --conan-storage
# epm venv active name
# epm venv uinstall name --force
# epm venv list name

class VEnv(Command):
    """
    EPM virtual environment manage command
    """
    name = 'venv'
    help = 'Virtual environment.'

    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):

        args = {
            'install': {
                'help': 'Unstall epm virtual environment.',
                'args': _install_args
            },
            'shell': {
                'help': 'Startup an install virtual environment shell.',
                'args': _active_args

            },
            'list': {
                'help': 'List installed venv.',
                'args': _list_args

            },
            'banner': {
                'help': 'Print banner of the venv.',
                'args': _banner_args

            },
            'uninstall': {
                'help': 'Uninstall specified environment',
                'args': _uninstall_args

            }
        }
        Command.__init__(self, args)

    def run(self, args, api=None):
        print(args)
        if args.sub_command == 'install':
            from epm.tool.venv import install
            install(args.location, args.install_dir)
        elif args.sub_command == 'shell':
            from epm.tool.venv import active
            active(args.name)
        elif args.sub_command == 'banner':
            print('---------------------XXXXXXXXXXXX', args)
            from epm.tool.venv import banner
            print(args.name)
            print(banner(args.name))


register_command(VEnv)
