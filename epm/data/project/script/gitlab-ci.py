import os
import re
import yaml
from jinja2 import Environment, BaseLoader
from epm.model.profile import load_profiles

__dir__ = os.path.abspath(os.path.dirname(__file__))

_family_prolog = """
# ================================================================
#          %s
# ================================================================
"""


class Config(object):

    def __init__(self):
        self._config = None
        self.profile = {}
        self.scheme = []
        self.job = 'spec'
        self.script = []
        self.install = []
        self._parse()

    def _parse(self):
        path = os.path.join(os.path.dirname(__file__), 'ci.yml')
        factory = load_profiles()
        with open(path) as f:
            config = yaml.safe_load(f)
        with open('package.yml') as f:
            package = yaml.safe_load(f)

        profile = package.get('configuration', {}).get('profile', {})
        diff = set(profile).difference(set(factory.profiles.keys()))
        if diff:
            raise Exception('package.yml profile %s not found in installed epm profiles' % diff)

        for family in profile:
            types = config.get('configuration', {}).get(family, {}).get('spec', None)
            self.profile[family] = factory.spec_names(family, types)

        self.scheme = list(package.get('configuration', {}).get('scheme', {}).keys())
        if 'default' not in self.scheme:
            self.scheme = ['default'] + self.scheme
        self.job = config.get('job', 'spec')
        self.docs = config.get('docs', 'false')
        self.pages = config.get('pages', 'false')
        self.install = config.get('test', {}).get('install', [])
        self.script = config.get('test', {}).get('script', [])


class Assembler(object):

    def __init__(self):
        self.config = Config()

    def _render(self, template, kwords):
        """ Render the template using keyword arguments as local variables. """

        try:
            jtemplate = Environment(loader=BaseLoader()).from_string(template)
            return jtemplate.render(kwords)
        except Exception as e:
            e.translated = False
            print("\n%s\n" % str(e))
            i = 1
            for line in template.split('\n'):
                print('%d:' % i, line)
                i += 1
            raise e

    def _template(self, family):

        GCC = re.compile(r'gcc\d$')
        HISI = re.compile(r'hisi\d+$')
        if family in ['vs2019', 'vs2017']:
            filename = 'visualstudio.yml.j2'
        elif GCC.match(family):
            filename = 'linux-gcc.yml.j2'
        elif HISI.match(family):
            filename = 'linux-hisi.yml.j2'
        elif family == 'prolog':
            filename = 'prolog.yml.j2'
        else:
            raise Exception('Unsupported profile %s' % family)
        path = os.path.join(os.path.dirname(__file__), 'ci', filename)
        with open(path) as f:
            return f.read()

    def generate(self):
        config = self.config
        kwords = {'me': './script/gitlab-ci.py'}
        content = self._render(self._template('prolog'), kwords)
        for family, specs in config.profile.items():
            kwords['title'] = family
            kwords['install'] = config.install
            kwords['script'] = config.script
            kwords['family'] = family
            template = self._template(family)
            cs = []
            content += _family_prolog % family
            for scheme in config.scheme:
                for spec in specs:
                    c = spec if scheme == 'default' else '%s@%s' % (spec, scheme)
                    cs.append(c)
                    if config.job == 'spec':
                        kwords['title'] = c
                        kwords['configurations'] = [c]
                        content += "#        ----    scheme: %s    ----\n" % scheme
                        content += self._render(template, kwords)
            kwords['configurations'] = cs

            if config.job == 'family':
                content += self._render(template, kwords)

        with open('.gitlab-ci.yml', 'w') as f:
            f.write(content)


if __name__ == '__main__':
    Assembler().generate()
