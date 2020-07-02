import os
from epm.commands import Command, register_command, ArgparseArgument


_INSTALL_LOCATION = \
    "location of the work environment source, it could be local directory or "\
    "url for tarball (.zip) of http/https."

_SHELL_NAME_HELP = "The name of install virtual environment."



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
                'args': [ArgparseArgument("location", type=str, help=_INSTALL_LOCATION)]
            },

            'shell': {
                'help': 'Startup work environment.',
                'args': [ArgparseArgument("name", default=None, type=str, help=_SHELL_NAME_HELP)]
            },

            'list': {
                'help': 'List all installed work environments.',
                'args': []
            },

            'show': {
                'help': 'Show specified work environment information.',
                'args': [ArgparseArgument("name", help="The name of the work environment.")]
            },

            'banner': {
                'help': 'Print banner of the work environment.',
                'args': [ArgparseArgument("name", nargs='?', default=None, type=str, help="The name wenv.")]

            },

            'uninstall': {
                'help': 'Uninstall specified work environment',
                'args': [ArgparseArgument("name", default=None, type=str, help="The name to be uninstalled.")]

            }
        }
        Command.__init__(self, args)

    def run(self, args, api=None):
        from epm.tools import wenv
        if args.sub_command == 'install':
            wenv.install(args.location, args.install_dir)
        elif args.sub_command == 'shell':
            wenv.active(args.name)
        elif args.sub_command == 'banner':
            from epm.tools.wenv import banner
            print(banner(args.name))
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
