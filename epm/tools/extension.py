import os
import sys
import argparse
import yaml
from collections import namedtuple
from epm.utils import abspath


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
    def prototype(self):
        P = namedtuple('Prototype', 'namespace name version url')
        p = self.metainfo.get('prototype')
        if not p:
            return None
        version = None
        namespace = None
        url = None
        if isinstance(p, str):
            tokens = p.split('=')
            if len(tokens) == 2:
                version = tokens[1]
            tokens = tokens[0].split(':')
            namespace = tokens[0]
            name = tokens[1]
        else:
            assert isinstance(p, dict)
            name = p['name']
            namespace = p.get('namespace') or namespace
            version = p.get('version')
            url = p.get('version')
        return P(namespace, name, version, url)

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
            path = f'~/.epm/.workbench/{workbench}' if workbench else f'~/.epm'
            path = f'{path}/extension/{namespace}/{name}'
            if not os.path.exists(path, Definition.METAINFO_MANIFEST):
                raise FileNotFoundError(f"extension <{namespace}:{name}> not found.")

        return Definition(path, where=where)


class Argument(object):
    TYPE = {'str': str, 'int': int}

    def __init__(self, definition):
        self._definition = definition

    def parse(self, argv):
        prog = self._definition.description
        parser = argparse.ArgumentParser(prog=prog)
        enums = {}
        if not argv or not self._definition.argument:
            return object()

        for name, prop in self._definition.argument.items():
            param = {}
            type = prop.get('type', 'str')
            if type:
                param['type'] = Argument.TYPE.get(type)

            default = prop.get('default', None)
            if default:
                param['default'] = default
                if type == 'str' and "{{" in default and "}}" in default:
                    param['default'] = Jinja2(self._config).parse(default)
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


class Prototype(object):

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

    def exec(self, argv=[], runner=None, extension_definition=None):
        raise NotImplemented(f"{self.defination.name} Prototype.exec not implemented.")


class Extension(object):

    def __init__(self, definition, prototype=None):
        self.definition = definition
        self.prototype = prototype
class Jinja(Extension)