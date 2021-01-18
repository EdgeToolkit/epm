import os
import sys
import argparse
import yaml
import glob
from collections import namedtuple
from conans.tools import chdir
from epm.utils import Jinja2 as J2


class Definition(object):
    METAINFO_MANIFEST = 'extension.yml'

    def __init__(self, path, where=None):
        Attribute = namedtuple('Attribute', ['dir', 'where'])
        self.attribute = Attribute(path, where)
        with open(os.path.join(self.attribute.dir, self.METAINFO_MANIFEST)) as f:
            self.metainfo = yaml.safe_load(f)

    @property
    def name(self):
        return self.metainfo.get('name') or ''

    @property
    def version(self):
        ver = self.metainfo.get('version')
        if ver is None:
            return ''
        return str(ver)

    @property
    def namespace(self):
        return self.metainfo['namespace']

    @property
    def kind(self):
        return self.metainfo.get('kind') or 'extension'

    @property
    def author(self):
        return self.metainfo.get('author')

    @property
    def email(self):
        return self.metainfo.get('email')

    @property
    def home(self):
        return self.metainfo.get('home')

    @property
    def topics(self):
        return self.metainfo.get('topics') or []

    @property
    def license(self):
        return self.metainfo.get('license') or []

    @property
    def entry(self):
        return self.metainfo.get('entry') or 'main.py'

    @property
    def description(self):
        return self.metainfo.get('description') or ''

    @property
    def argument(self):
        return self.metainfo.get('argument', []) or []

    def __contains__(self, item):
        return item in self.metainfo

    def __getitem__(self, i):
        return self.metainfo.get(i)

    @staticmethod
    def load(name, namespace=None, project=None, workbench=None):
        where = None
        path = None
        from epm.utils import abspath
        if project and project.metainfo and namespace is None:
            data = project.metainfo.get('extension') or {}
            if name in data:
                config = data.get(name) or {}
                path = config.get('path') or f'extension/{name}'
                path = abspath(os.path.join(project.dir, path))
                where = 'package'
                if not os.path.exists(path, Definition.METAINFO_MANIFEST):
                    raise FileNotFoundError("extension <{name}> defined in meta-info file,"
                                            "but definition file {path} not found.")

        if where is None:
            namespace = namespace or 'epm'
            path = f'~/.epm/.workbench/{workbench}' if workbench else '~/.epm'
            path = abspath(f'{path}/.extension/{namespace}/{name}')
            if not os.path.exists(f"{path}/{Definition.METAINFO_MANIFEST}"):
                raise FileNotFoundError(f"extension <{namespace}:{name}> not found."
                                        f"{path}/{Definition.METAINFO_MANIFEST}")

        return Definition(path, where=where)


class Argument(object):
    TYPE = {'str': str, 'int': int}

    def __init__(self, definition):
        self._definition = definition

    def parse(self, argv):
        prog = self._definition.description
        parser = argparse.ArgumentParser(prog=prog)
        enums = {}
        if not self._definition.argument:
            return object()
        argv = argv or []

        for name, prop in self._definition.argument.items():
            param = {}
            type = prop.get('type', 'str')
            if type:
                param['type'] = Argument.TYPE.get(type)

            default = prop.get('default', None)
            if default:
                param['default'] = default
                if type == 'str' and "{{" in default and "}}" in default:
                    param['default'] = J2().parse(default)
            else:
                param['required'] = True

            help = prop.get('help', None)
            if help:
                param['help'] = help
            parser.add_argument(f"--{name}", **param)
            enum = prop.get('enum', None)
            if enum:
                enums[name] = enum
        args = parser.parse_args(argv)
        for name, items in enums.items():
            symbol = name.replace('-', '_')
            value = getattr(args, symbol)
            if value not in items:
                raise Exception(f"options --{name} should be in {items}".format(
                    name=name, items=items))
        return args


class Extension(object):

    def __init__(self, definition):
        self.definition = definition

    @property
    def name(self):
        return self.definition.name

    @property
    def namespace(self):
        return self.definition.namespace

    def parse_args(self, argv):
        argument = Argument(self.definition)
        return argument.parse(argv)

    def exec(self, argv=[], runner=None):
        raise NotImplemented(f"{self.defination.name} Prototype.exec not implemented.")


class JinjaExtension(Extension):
    TEMPLATE_DIR = 'templates'

    def __init__(self, definition):
        super().__init__(definition)
        self._context = {}

    def exec(self, argv=[], runner=None):
        args = self.parse_args(argv)
        for item in self.definition['template'] or []:
            self._compile(item, args)

    def _compile(self, item, args):

        if_expr = None
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

        path = os.path.join(self.definition.attribute.dir, 'templates', src)
        if os.path.isfile(path):
            self._generate(args, src, dst)

        elif os.path.isdir(path):
            files = []
            with chdir(f"{self.definition.attribute.dir}/{self.TEMPLATE_DIR}"):
                for i in glob.glob('*'):
                    if os.path.isfile(i):
                        files.append(i)
            for i in files:
                self._generate(args, i, dst)
        else:
            msg = f'template source file {path} '
            msg += 'is invalid' if os.path.exists(path) else 'not exists.'
            raise Exception(msg)

    def _if(self, expr, args):
        if isinstance(expr, str):
            expr = [expr]
        values = {'argument': args}
        for e in expr:
            try:
                result = eval(e, values)
            except:
                print('Parse condition statement error.\n+', e)
                raise
            if not result:
                return False
        return True

    def _generate(self, args, src, dst):
        path = dst or src
        path = J2(self._context).parse(path, {'argument': args})
        outfile = os.path.join(args.out, path)
        template_dir = os.path.join(self.definition.attribute.dir, 'templates')
        j2 = J2(template_dir, context=self._context)
        j2.render(src, context={'argument': args}, outfile=outfile)


