import os
from epm.commands import Command, register_command, ArgparseArgument

_install_args = [

    ArgparseArgument("location", type=str,
                     help="location of the install source, support local directory or http/hppts zip url."),

    ArgparseArgument("-e", "--editable", default=False, action='store_true',
                     help="(for debug only) where to installed, by default it will be installed on ~/.epm/wenv/{name}"),
]

_active_args = [
    ArgparseArgument("name", default=None, type=str,
                     help=""),
]

_show_args = [
    ArgparseArgument("name", help=""),
]

_banner_args = [
    ArgparseArgument("name", nargs='?', default=None, type=str,
                     help="The name wenv."),
]

_uninstall_args = [
    ArgparseArgument("name", default=None, type=str,
                     help=""),
]


class WorkEnvironment(Command):
    """
    EPM workbench management command
    """
    name = 'workbench'
    help = 'Workbench environment.'

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
        from epm.util.workbench import install, active, banner
        if args.sub_command == 'install':
            install(args.location, args.editable)
        elif args.sub_command == 'shell':
            active(args.name)
        elif args.sub_command == 'banner':
            banner()

        #############################################################
        elif args.sub_command == 'list':
            info = wenv.get_all_installed_wenv_info()
            print('{:19s} {:40s}'.format('name', 'location'))
            print('{:19s} {:40s}'.format('-'*19, '-'*40))
            for name, value in info.items():
                print('{:19s} {:40s}'.format(name, os.path.normpath(value['location'])))
        elif args.sub_command == 'show':
            info = wenv.get_all_installed_wenv_info()
            info = info.get(args.name)
            if info:
                print(info['config']['wenv'].get('description'))
            else:
                print('%s not installed.' % args.name)


register_command(WorkEnvironment)
