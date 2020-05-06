import os
from epm.commands import Command, register_command, ArgparseArgument

_install_args = [

    ArgparseArgument("location", type=str,
                     help="location of the install source, support local directory or http/hppts zip url."),

    ArgparseArgument("--install-dir", type=str, default=None,
                     help="where to installed, by default it will be installed on ~/.epm/wenv/{name}"),
]

_active_args = [
    ArgparseArgument("name", default=None, type=str,
                     help="The name of install virtual environment."),
]

_show_args = [
    ArgparseArgument("name", help="The name of the wenv to be display."),
]

_banner_args = [
    ArgparseArgument("name", nargs='?', default=None, type=str,
                     help="The name wenv."),
]

_uninstall_args = [
    ArgparseArgument("name", default=None, type=str,
                     help="The name to be uninstalled."),
]


class WorkEnvironment(Command):
    """
    EPM work environment manage command
    """
    name = 'wenv'
    help = 'Work environment.'

    def __init__(self):

        args = {
            'install': {
                'help': 'Install epm work environment.',
                'args': _install_args
            },
            'shell': {
                'help': 'Startup an installed work environment shell.',
                'args': _active_args

            },
            'list': {
                'help': 'List all installed work environment.',
                'args': []

            },
            'show': {
                'help': 'Show specified work environment information.',
                'args': _show_args

            },

            'banner': {
                'help': 'Print banner of the work environment.',
                'args': _banner_args

            },
            'uninstall': {
                'help': 'Uninstall specified work environment',
                'args': _uninstall_args

            }
        }
        Command.__init__(self, args)

    def run(self, args, api=None):
        if args.sub_command == 'install':
            from epm.tool.wenv import install
            install(args.location, args.install_dir)
        elif args.sub_command == 'shell':
            from epm.tool.wenv import active
            active(args.name)
        elif args.sub_command == 'banner':
            from epm.tool.wenv import banner
            print(banner(args.name))
        elif args.sub_command == 'list':
            from epm.tool.wenv import get_all_installed_venv_info
            info = get_all_installed_venv_info()
            print('{:19s} {:40s}'.format('name', 'location'))
            print('{:19s} {:40s}'.format('-'*19, '-'*40))
            for name, value in info.items():
                print('{:19s} {:40s}'.format(name, os.path.normpath(value['location'])))
        elif args.sub_command == 'show':
            from epm.tool.wenv import get_all_installed_venv_info
            info = get_all_installed_venv_info()
            info = info.get(args.name)
            if info:
                print(info['config']['wenv'].get('description'))
            else:
                print('%s not installed.' % args.name)


register_command(WorkEnvironment)
