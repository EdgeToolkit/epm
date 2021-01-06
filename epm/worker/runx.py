import sys
import os
import shutil
import subprocess
from conans.client.tools import ConanRunner
from conans.tools import rmdir


from epm.worker import Worker
import copy

def cache(path):
    url = urlparse(path)
    folder = path
    download_dir = tempfile.mkdtemp(suffix='epm.wenv')

    if url.scheme in ['http', 'https']:
        filename = os.path.join(download_dir, os.path.basename(path))
        urllib.request.urlretrieve(path, filename)
        folder = os.path.join(download_dir, 'wenv.config')
        zfile = zipfile.ZipFile(filename)
        zfile.extractall(folder)
    elif url.scheme.startswith('git+'):
        url = path[4:]
        fields = url.split('@')
        options = ['--depth', '1']
        if len(fields) > 1:
            url = fields[0]
            branch = fields[-1]
            options += ['-b', branch]

        subprocess.run(['git', 'clone', url, download_dir] + options)
        rmdir(os.path.join(download_dir, '.git'))
        folder = download_dir

    if not os.path.exists(folder):
        raise Exception('Invalid install path {}'.format(path))
    return folder




"""
app:
  <name>:
    dir: test_package
    buildx
    
  <name2>:
    dir: teszz
    
extension:
  {name}:
    dir: ./extension/{name} #relative to this package root directory (opt)
    purpose: general | package
    factory: false
    

"""
class Runner(object):

    def __init__(self, sandbox, name=None):
        self._name = name
        self._sandbox = sandbox
        self._project = sandbox.project
        self._profile = self._project.profile
        self._api = self._project.api
        self._config = self._sandbox.api.load_config()
        self._runner = None
        if not name:
            self._runner = self._profile.docker.runner
            name = 'docker' if self._runner else 'shell'
        else:
            if name not in ['shell', 'docker']:
                self._runner = self._config.get('runner', {}).get(name)
                if not self._runner:
                    raise Exception('<%s> not defined in config file runner section.' % name)
        self._name = name

        # TODO: add validation of being runnable for this profile

    def exec(self, command, argv):
        runner = ConanRunner(output=self._api.out)
        command = '{} {}'.format(" ".join(command), " ".join(argv))
        return runner(command)
import yaml
from collections import namedtuple


class ExtensionDefinition(object):
    METAINFO_MANIFEST = 'extension.yml'

    def __init__(self, dir='.', purpose='general', origin='global'):
        Attribute = namedtuple('Attribute', ['dir', 'purpose', 'origin'])
        self.attribute = Attribute(os.path.abspath(dir),
                                   purpose, origin)
        with open(os.path.join(self.attribute.dir, ExtensionDefinition.METAINFO_MANIFEST)) as f:
            self.matainfo = yaml.safe_load(f)

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
        return ExtensionDefinition(**attribute)



class RunX(Worker):

    def __init__(self, name, project=None, api=None):
        super(RunX, self).__init__(api)
        self.name = name
        self.project = project
        self.WD = os.path.abspath('.')
        self.definition = ExtensionDefinition.load(name)

    def exec(self, runner=None, argv=[]):

