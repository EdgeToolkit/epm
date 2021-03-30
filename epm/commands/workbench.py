import os
import tempfile

from epm.commands import Command, register_command, ArgparseArgument

from epm.errors import EException
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


class Workbench(Command):
    """
    EPM workbench management command
    """
    name = 'workbench'
    help = 'Workbench environment manipulate command.'

    def __init__(self):

        argsx = {
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

        args = [
            ArgparseArgument("name", type=str, nargs='?',
                             help="name of the workbench."),

            ArgparseArgument("--action", type=str, default='active',
                             choices=['install', 'uninstall', 'list', 'show', 'active'],
                             help="action for specified workbench")

        ]

        Command.__init__(self, args)

    def run(self, args, api=None):
        from epm.utils import workbench
        if args.action == 'active':
            workbench.active(args.name)
        elif args.action == 'install':
            if not args.name:

                raise EException('Not specified location of workbench tarball/path')
            workbench.install(args.name)
        elif args.action == 'list':
            info = workbench.get_all_installed_wenv_info()
            print('{:19s} {:40s}'.format('name', 'location'))
            print('{:19s} {:40s}'.format('-' * 19, '-' * 40))
            for name, value in info.items():
                print('{:19s} {:40s}'.format(name, os.path.normpath(value['location'])))


class Workbench(Command):
    """
    EPM workbench management command
    Usage:
    
    * Install workbench form local path or url (http https or git (vcs url)
      epm workbech install <url>
      epm workbech install <local project path>
      
    * List all installed workbench
      epm worbench list
      
    * display workbench description
      epm workbench desc <workbench name >
      
    * active workbench
      epm workbench active <name>
      epm workbench <name>    
    """
    name = 'workbench'
    help = 'Workbench environment manipulate command.'
    
    prog = ''

    def __init__(self):
            args = [
                ArgparseArgument("name_or_subcommand", nargs='*' ,
                                  help="Active workbench or install/list/display workbench(s) see usage."),
                ]
            Command.__init__(self, args)
        
    def run(self, args, api=None):
        
        if args.name_or_subcommand:
            cmd= args.name_or_subcommand[0]
            param = args.name_or_subcommand[1:] 
            if cmd == 'install':
                self._install(param)
            elif cmd == 'list':
                self._list(param)
            elif cmd == 'desc':
                self._desc(param)
            elif cmd == 'active':
                self._active(param)
            else:
                self._active([cmd])   
        else:
            from epm.utils import workbench
            name = os.getenv('EPM_WORKBENCH') or ''
            workbench.active(name, dry_run=True)

    def _install(self, param):
        if len(param) < 1:
            print('workbench source url/path not specified.')
            sys.exit(1)
        url = param[0]        
        
        from urllib.parse import urlparse
        parser = urlparse(url)
        path = url
        subdir = None
        branch = None
        giturl = None
        if parser.scheme:
            tmpd = tempfile.mkdtemp()
            if parser.scheme.startswith('git'):
                gitpath=parser.path.split('@')
                if len(gitpath)>1:
                    branch=gitpath[1]
                    gitpath=gitpath[0]
                else:
                    gitpath=parser.path
                giturl = f"{parser.scheme}://{parser.netloc}/{gitpath}"

                for field in parser.fragment.split('&'):
                    k,v = field.split('=')
                    if k=='subdirectory':
                        subdir=v
                from subprocess import run
                run(['git', 'clone', giturl[4:], tmpd])
                from conans.tools import chdir
                with chdir(tmpd):
                    run(['git', 'checkout', '-b', 'branch', '--track', f'origin/{branch}'])
                    path=os.path.join(tmpd, subdir) if subdir else tmpd
                
            elif parser.scheme in ['http', 'https']:
                from conans.tools import get
                get(url, tmpd)
                path=tmpd
        from epm.utils import workbench
        name = None if len(param) < 2 else param[1]
        workbench.install(path, name)
    def _list(self, param):
        from epm import HOME_DIR
        wd = os.path.join(HOME_DIR, '.workbench')
        workbenchs = []
        if os.path.exists(wd):
            for i in os.listdir(wd):
                if os.path.exists(f"{wd}/{i}/config.yml"):
                    workbenchs.append(i)
        if workbenchs:
            for i in workbenchs:
                print(f"  {i}")
        else:
            print('No workbench installed.')
            
    def _desc(self, param):
        print('Not implemented')
        
    def _active(self, param):
        if len(param) < 1:
            print('workbench name not specified.')
            sys.exit(2)
        from epm.utils import workbench
        workbench.active(param[0])
        
    
                
                
        
            
register_command(Workbench)
