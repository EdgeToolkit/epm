import os
from epm.commands import Command, register_command, ArgparseArgument
from epm.errors import ECommandError

_generate_args = [
    ArgparseArgument("template", type=str,
                     help="The template which used to generate project skeleton."),

    ArgparseArgument("--name", default=None, type=str,
                     help="name of the package, if not specified use the folder name."),

    ArgparseArgument("--version", type=str, default='0.0.1',
                     help="version of the package, if not specified use default value 0.0.1"),
]

_show_template_args = [
    ArgparseArgument("name", type=str,
                     help="The name of the project template to be shown."),

]

_install_template_args = [
    ArgparseArgument("url", default=None, type=str,
                     help="The location of the project template."),
    ArgparseArgument("-e", "--editable", default=False, action='store_true',
                     help='Install a project template in editable mode from a local path.'),
]


class Project(Command):
    """
    """

    name = 'project'
    help = 'Project manager for epm package development.'
    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):

        args = {
            'gen': {
                'help': 'Generate C/C++ project according specified template.',
                'args': _generate_args
            },
            'install': {
                'help': 'Install project (template) from specified url (http or local zip file)',
                'args': _install_template_args

            },
            'list': {
                'help': 'List all installed project (templates).'
            },
            'show': {
                'help': 'Show information about the installed project (template)',
                'args': _show_template_args

            }
        }
        Command.__init__(self, args)

    def run(self, args, api):
        from epm.tools.project import load_project_templates_manifest, generate_project
        templates = load_project_templates_manifest()

        if args.sub_command in ['gen', 'generate']:
            manifest = templates.get(args.template, None)
            if manifest is None:
                raise ECommandError('project template <%s> not exists' % args.name)
            import os
            name = args.name or os.path.basename(os.path.abspath('.'))

            generate_project(manifest, {
                'name': name,
                'version': args.version
            })
        elif args.sub_command == 'install':
            self._install(args.url, args.editable)
        elif args.sub_command == 'list':
            print('{:20s} {:40s}'.format('name', 'location'))
            print('-'*20, '-'*40)
            for name, value in templates.items():
                print('{:20s} {:40s}'.format(name, value['dir']))
                desc = value.get('description', '')
                lines = desc.split("\n")
                indent = ' '*20 + '\n'
                print('{:20s} {}'.format('', indent.join(lines)))

        elif args.sub_command == 'show':
            manifest = templates.get(args.name, None)
            if manifest is None:
                print('project template <%s> not exists' % args.name)
            else:
                print(manifest.get('description'))

    def _install(self, url, editable):
        editable = bool(editable)
        folder = url
        if os.path.isdir(url):
            url = os.path.abspath(url)
        else:
            editable = False

        import yaml
        from epm.paths import HOME_EPM_DIR

        with open(os.path.join(folder, '.manifest.yml')) as f:
            manifest = yaml.safe_load(f)
        name = manifest['name']

        prjd = os.path.join(HOME_EPM_DIR, 'projects')
        if not os.path.exists(prjd):
            os.makedirs(prjd)

        path = os.path.join(prjd, name)
        if os.path.exists(path):
            raise ECommandError('project template %s already installed' % name)

        if editable:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump({'location': folder}, f)





register_command(Project)
