import os
import sys
import argparse
import yaml
from jinja2 import Environment, FileSystemLoader, BaseLoader


def If(expr, args):
    symbol = {}
    params = vars(args)  # 返回 args 的属性和属性值的字典
    for k, v in params.items():
        symbol[f"argument.{k}"] = v
    from epm.utils.yacc.condition import Yacc
    yacc = Yacc(symbol)

    result = yacc.parse(expr)
    return result


class Jinja2(object):

    def __init__(self, directory):
        self._dir = os.path.abspath(os.path.expanduser(directory))

    def _add_filters(self, env):
        def _basename(path):
            return os.path.basename(path)

        env.filters['basename'] = _basename
        return env

    def render(self, template, context={}, outfile=None, trim_blocks=True):

        env = Environment(loader=FileSystemLoader(self._dir))

        env.trim_blocks = trim_blocks
        self._add_filters(env)
        T = env.get_template(template)
        text = T.render(context)
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
        return T.render(**context)


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


class Extension(object):
    _KIND = {}
    prototype = None

    def __init__(self, directory, cwd=None, prototype=None):
        self._dir = os.path.abspath(os.path.expanduser(directory))
        self._wd = os.path.abspath(cwd or '.')
        path = os.path.join(self._dir, 'extension.yml')
        with open(path) as f:
            self._config = yaml.safe_load(f)
            self._config['__file__'] = path
        self._argument = Argument(self._config)
        self._context = {'WD': self._wd,
                         'name': self._config['name'],
                         'version': self._config.get('version', ''),
                         'description': self._config.get('description', '')
        }
        self._args = None
        self.prototype = self._load_prototype()

    def _load_prototype(self):
        name = self._config.get('prototype', None)
        if not name:
            return None
        directory = os.path.expanduser('~/.epm/extension/.prototype/{name}')
        path = os.path.join(directory, 'prototype.yml')
        if not os.path.exists(path):
            raise FileNotFoundError(f'prototype <{name}> defination file {path} not exists.')

        return Prototype(directory)

    def exec(self, argv):
        self._args = self._argument.parse(argv)
        if self.prototype:
            return self.prototype.exec(argv)


class Jinja(Extension):

    def __init__(self, directory):
        super().__init__(directory)

    def exec(self, argv):
        super().exec(argv)
        for item in self._config.get('template') or []:
            self._compile(item, self._args)

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

        path = os.path.join(self._dir, 'templates', src)
        if os.path.isfile(path):
            self._generate(args, src, dst)
        elif os.path.isdir(path):
            from conans.tools import chdir
            tfiles = []
            with chdir(f"{self._dir}/templates"):
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

        def _jpath(x):
            return Jinja2(self._dir).parse(dst, context)
        #infile = os.path.join(self._dir, 'templates', src)
        outfile = os.path.join(args.out, _jpath(dst or src))
        j2 = Jinja2(os.path.join(self._dir, 'templates'))
        j2.render(src, context, outfile=outfile)



def main(argv):
    pass

if __name__ == '__main__':
    print(sys.argv)

#
#
#ext = TemplateExtension(r'D:\_download\mkprj')
#ext.exec(['--type', 'lib'])
#import sys
#sys.exit(0)
#
#def load_config(path):
#    path = os.path.abspath(os.path.expanduser(path))
#    with open(path) as f:
#        conf = yaml.safe_load(f)
#        conf['__file__'] = path
#    return conf
#
#
#
#
#conf = load_config(r'D:\_download\mkprj\extension.yml')
#j2 = Jinja2(conf)
#txt = j2.parse(conf['argument']['dir']['default'])
#print('*', conf['argument']['dir']['default'])
#print('-->', txt)
#
#arg = Argument(conf)
#print(arg.parse(['--type', 'libx']))
#
#