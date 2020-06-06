import os
import yaml
import sys
import shutil
from string import Template
from epm.util.files import mkdir
from jinja2 import PackageLoader, Environment, FileSystemLoader
from epm.paths import HOME_EPM_DIR, DATA_DIR
from epm.model.runner import Output

class Creator(object):

    def __init__(self, manifest, param):
        self._dir = manifest['dir']
        self._files = manifest['files']
        self._meta = dict(param, **{'manifest': manifest})

    @property
    def artifacts(self):
        def _(templ):
            s = Template(templ)
            return s.substitute(self._meta)

        results = []
        for item in self._files:
            if isinstance(item, str):
                item = _(item)
                filename = os.path.join(self._dir, item)
                if os.path.exists(filename + '.j2'):
                    results.append((item + '.j2', item, 'jinja'))
                elif os.path.exists(filename):
                    results.append((item, item, ''))
                else:
                    raise Exception('illegal item %s' % item)
            elif isinstance(item, dict):
                for k, v in item.items():
                    assert isinstance(v, str)
                    assert isinstance(k, str)
                    k = _(k)
                    v = _(v)
                    j2 = 'jinja' if v.endswith('.j2') else ''
                    filename = os.path.join(self._dir, v)
                    if not os.path.exists(filename):
                        raise Exception('not exists template file %s' % filename)
                    results.append((v, k, j2))
            else:
                raise Exception('unsupported %s %s' % (item, type(item)))
        return results

    def copy(self, src, dst):
        folder = os.path.dirname(dst)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        import shutil
        shutil.copyfile(os.path.join(self._dir, src), dst)

    def jinja(self, src, dst):
        folder = os.path.dirname(os.path.join(self._dir, src))
        env = Environment(loader=FileSystemLoader(folder))
        template = env.get_template(os.path.basename(src))
        content = template.render(self._meta)

        folder = os.path.dirname(dst)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with open(dst, 'w') as f:
            f.write(content)

    def run(self):
        for src, dst, type in self.artifacts:
            #print(src, dst, bool(type))
            print('-- %s' % dst)
            if type == 'jinja':
                self.jinja(src, dst)
            else:
                self.copy(src, dst)


def load_project_templates_manifest():
    dirs = [os.path.join(DATA_DIR, 'projects', '__builtin__')]
    folder = os.path.join(os.path.join(HOME_EPM_DIR, 'projects'))
    if os.path.isdir(folder):
        for d in os.listdir(folder):
            path = os.path.join(folder, d)
            if os.path.isfile(path):
                with open(path) as f:
                    data = yaml.safe_load(f)
                    path = data['location']
                    assert os.path.isdir(path)

            if os.path.isdir(path) and os.path.exists(os.path.join(path, '.manifest.yml')):
                dirs.append(path)

    results = {}

    for d in dirs:
        filename = os.path.join(d, '.manifest.yml')
        with open(filename) as f:
            manifest = yaml.safe_load(f)
            files = manifest.get('files')
            description = manifest.get('description')
            templates = manifest.get('templates')
            group = manifest['name']
            if templates:
                for k, v in templates.items():
                    name = k if group in ['__builtin__'] else '%s@%s' % (k, group)
                    description = v['description']
                    files = v['files']
                    results[name] = {
                        'name': name,
                        'fullname': '%s@%s' % (k, group),
                        'group': group,
                        'type': k,
                        'dir': d,
                        'files': files,
                        'description': description
                    }
            else:
                results[group] = {
                    'name': group,
                    'fullname': group,
                    'dir': d,
                    'files': files,
                    'description': description
                }
    return results


def generate_project(manifest, param):
    if isinstance(manifest, str):
        templates = load_project_templates_manifest()
        manifest = templates[manifest]
    gen = Creator(manifest, param)
    gen.run()



