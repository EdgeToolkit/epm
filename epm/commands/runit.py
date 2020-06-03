from epm.commands import Command, register_command, ArgparseArgument


class Run(Command):
    """
    """

    name = 'run'
    help = 'Execute command in epm running environment.'
    #prog = 'epm [-p PROFILE] [-s SCHEME] [-r RUNNER] %s' % name

    def __init__(self):
        args = [

            ArgparseArgument("run_command", type=str,
                             help="The command that defined in package.yml script section.")
            ]

        Command.__init__(self, args)

    def run(self, args, api):
        param = self.parameter(args)
        param['command'] = args.run_command
        param['args'] = args.argv
        print(param, '\n----', __file__)
        import subprocess
        p = subprocess.run(['echo', 'ABCDEFG'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
        print('Stdout->', p.stdout)
        print('==END subprocess', p.returncode)
        return api.runit(param)

register_command(Run)
