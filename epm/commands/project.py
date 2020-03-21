"""
epm project create lib --name xxx --version 0.1.2

epm project install-template http://kedacom.com/xxx.zip

epm project list-templates

epm project show <template name>
"""


from epm.commands import Command, register_command, ArgparseArgument

_generate_args = [
    ArgparseArgument("template", default=None, type=str,
                     help="The template which used to generate project skeleton."),

    ArgparseArgument("--name", default=None, type=str,
                     help="name of the package, if not specified use the folder name."),

    ArgparseArgument("--version", type=str, default='0.0.1',
                     help="version of the package, if not specified use default value 0.0.1"),
]

_show_template_args = [
    ArgparseArgument("template", default=None, type=str,
                     help="The template to be shown."),

]

_install_template_args = [
    ArgparseArgument("url", default=None, type=str,
                     help="The location of the template tarball."),
]


class Project(Command):
    """
    """

    name = 'project'
    help = 'Project manager for epm package development.'
    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):

        args = {
            'generate': {
                'help': 'Generate C/C++ project for epm package base on specified template.',
                'args': _generate_args
            },
            'install-template': {
                'help': 'Install template from specified url (http or local zip file)',
                'args': _install_template_args

            },
            'list-template': {
                'help': 'List all installed templates.'
            },
            'show-template': {
                'help': 'Display the specified template infomation',
                'args': _show_template_args

            }
        }
        Command.__init__(self, args)

    def run(self, args):
        print(args)



register_command(Project)
