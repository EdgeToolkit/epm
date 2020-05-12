from epm.commands import Command, register_command, ArgparseArgument


class Sandbox(Command):
    """
    """

    name = 'sandbox'
    help = 'Sandbox to execute build/create binary package.'
    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
        args = [

            ArgparseArgument("sandbox_command", type=str,
                             help="The sandbox command witch defined in package.yml sandbox section.")
            ]

        Command.__init__(self, args)

    def run(self, args, api):
        if args.sandbox_command == 'create':
            self._create(args, api)
            return
        param = self.parameter(args)
        param['command'] = args.sandbox_command
        param['args'] = args.argv

        api.sandbox(param)

    def _create(self, args, api):
        import argparse
        parser = argparse.ArgumentParser(description='Sandbox buildin create.')
        parser.add_argument('name', nargs='*',
                            help='sandbox items to be created')
        parser.add_argument('-c', '--configure', default=None, action='store_true',
                            help='execute configure step')
        parser.add_argument('-m', '--make', default=None, action='store_true',
                            help='execute make step')

        param = parser.parse_args(args.argv)
        program = param.name or None
        steps = []
        if args.configure:
            steps += ['configure']
        if args.make:
            steps += ['make']
        steps = steps or None

        from epm.worker.sandbox import Builder as SB
        from epm.model.project import Project
        project = Project(args.PROFILE, args.SCHEME, api=api)
        sb = SB(project)
        sb.exec(program, steps)







register_command(Sandbox)
