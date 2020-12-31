import os
import argparse
import yaml
from jinja2 import Environment, FileSystemLoader, Template, BaseLoader


class Jinja2(object):

    def __init__(self, config):
        self._config = config

    @property
    def context(self):
        context = {'WD': os.path.abspath('.'),
                   'name': self._config['name'],
                   'version': self._config.get('version', ''),
                   'description': self._config.get('description', '')
        }
        return context

    def _add_filters(self, env):
        def _basename(path):
            return os.path.basename(path)

        env.filters['basename'] = _basename
        return env

    def _extend_context(self, context={}):
        _context = {'WD': os.path.abspath('.'),
                    'name': self._config['name'],
                    'version': self._config.get('version', ''),
                    'description': self._config.get('description', '')
                   }
        _context.update(context)
        print(_context)
        return _context

    def render(self, template, context={}, outfile=None, trim_blocks=True):
        path = os.path.dirname(self._config['__file__'])
        env = Environment(loader=FileSystemLoader(path))

        env.trim_blocks = trim_blocks
        self._add_filters(env)
        T = env.get_template(template)
        text = T.render(self._extend_context(context))
        if outfile:
            path = os.path.abspath(outfile)
            folder = os.path.dirname(path)
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(path, 'w') as f:
                f.write(text)
        return text

    def parse(self, text, context={}):
        env = Environment(loader=BaseLoader())
        self._add_filters(env)
        T = env.from_string(text)
        return T.render(**self._extend_context(context))


class Argument(object):
    TYPE = {'str': str, 'int': int}

    def __init__(self, config):
        self._config = config
        self._argument = config.get('argument')

    def parse(self, argv):
        prog = self._config.get('description', "")
        parser = argparse.ArgumentParser(prog=prog)
        enums = {}

        for name, prop in self._argument.items():
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


def load_config(path):
    path = os.path.abspath(os.path.expanduser(path))
    with open(path) as f:
        conf = yaml.safe_load(f)
        conf['__file__'] = path
    return conf

conf = load_config(r'D:\_download\mkprj\extension.yml')
j2 = Jinja2(conf)
txt = j2.parse(conf['argument']['dir']['default'])
print('*', conf['argument']['dir']['default'])
print('-->', txt)

arg = Argument(conf)
print(arg.parse(['--type', 'libx']))
