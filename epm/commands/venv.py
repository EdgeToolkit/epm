import os
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

_show_args = [
    ArgparseArgument("name", help="The name of the venv to be display."),
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
                'help': 'List all installed venv.',
                'args': []

            },
            'show': {
                'help': 'Show specified venv information.',
                'args': _show_args

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
        if args.sub_command == 'install':
            from epm.tool.venv import install
            install(args.location, args.install_dir)
        elif args.sub_command == 'shell':
            from epm.tool.venv import active
            print('---', args)
            active(args.name)
        elif args.sub_command == 'banner':
            from epm.tool.venv import banner
            print(banner(args.name))
        elif args.sub_command == 'list':
            from epm.tool.venv import get_all_installed_venv_info
            info = get_all_installed_venv_info()
            print('{:19s} {:40s}'.format('name', 'location'))
            print('{:19s} {:40s}'.format('-'*19, '-'*40))
            for name, value in info.items():
                print('{:19s} {:40s}'.format(name, os.path.normpath(value['location'])))
        elif args.sub_command == 'show':
            from epm.tool.venv import get_all_installed_venv_info
            info = get_all_installed_venv_info()
            info = info.get(args.name)
            if info:
                print(info['config']['venv'].get('description'))
            else:
                print('%s not installed.' % args.name)



register_command(VEnv)
