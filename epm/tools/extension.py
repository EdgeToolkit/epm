import os
import sys
import argparse
import yaml
from collections import namedtuple


class Definition(object):
    METAINFO_MANIFEST = 'extension.yml'

    def __init__(self, dir='.', purpose='general', origin='global'):
        Attribute = namedtuple('Attribute', ['dir', 'purpose', 'origin'])
        self.attribute = Attribute(os.path.abspath(dir),
                                   purpose, origin)
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
    def description(self):
        return self.metainfo.get('description') or ''

    @property
    def argument(self):
        return self.metainfo.get('argument', []) or []



    @staticmethod
    def load(name, project=None, workbench=None):
        workbench = workbench or os.getenv('EPM_WORKBENCH', None)
        attribute = None
        if project and project.metainfo:
            data = project.metainfo.get('extension') or {}
            if name in data:
                attribute = dict({'purpose': 'package',
                                  'dir': os.path.join(project.dir, 'extension', name),
                                  'origin': 'package'
                                  }, **data)
                path = os.path.join(attribute['dir'], ExtensionDefinition.METAINFO_MANIFEST)
                if not os.path.exists(path):
                    raise Exception("extension <{name}> defined in meta-info file,"
                                    "but definition file {path} not found.")
        if attribute is None and workbench:
            path = os.path.expanduser(f'~/.epm/.workbench/{workbench}/extension/{name}/extension.yml')
            if os.path.exists(path):
                attribute = {'purpose': 'general',
                             'dir': os.path.dirname(path),
                             'origin': 'workbench'
                            }
        if attribute is None:
            path = os.path.expanduser(f'~/.epm/extension/{name}/extension.yml')
            if os.path.exists(path):
                attribute = {'purpose': 'general',
                             'dir': os.path.dirname(path),
                             'origin': 'global'
                            }
        return Definition(**attribute)


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



    def parse_args(self, argv):
        argument = Argument(self.definition)
        return argument.parse(argv)

    def exec(self, argv=[], runner=None):
        raise NotImplemented(f"{self.defination.name} Prototype.exec not implemented.")



