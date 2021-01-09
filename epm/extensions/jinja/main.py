import os
from epm.tools.extension import Prototype
from epm.tools import Jinja2 as J2


class Jinja(Prototype):

    def __init__(self, definition):
        super().__init__(definition)
        self._context = {}

    def exec(self, argv, runner):
        args = self.parse_args(argv)
        for item in self.definition.get('template') or []:
            self._compile(item, args)

    def _compile(self, item, args):

        if_expr = None
        src = None
        dst = None
        if isinstance(item, dict):
            src = item['src']
            dst = item.get('dst', None)
            if_expr = item.get('if', None)
        elif isinstance(item, str):
            src = item
        else:
            raise SyntaxError('unsupported template type {}'.format(type(item)))

        if if_expr and not self._if(if_expr, args):
            return

        path = os.path.join(self.defination.attribute.dir, 'templates', src)
        if os.path.isfile(path):
            self._generate(args, src, dst)
        elif os.path.isdir(path):
            from conans.tools import chdir
            tfiles = []
            with chdir(f"{self.defination.attribute.dir}/templates"):
                for root, dirs, files in os.listdir('.'):
                    for i in files:
                        tfiles.append(os.path.join(root, i))
            for i in tfiles:
                self._generate(args, i, dst)
        else:
            assert False

    def _if(self, expr, args):
        if isinstance(expr, str):
            expr = [expr]
        values = {'argument': args}
        for e in expr:
            if not eval(e, values):
               return False
        return True

    def _generate(self, args, src, dst):
        context = dict(self._context, **{'argument': args})
        path = dst or src
        path = J2().parse(path, context)
        outfile = os.path.join(args.out, path)
        template_dir = os.path.join(self.definition.attribute.dir, 'templates')
        j2 = J2(template_dir)
        j2.render(src, context, outfile=outfile)
