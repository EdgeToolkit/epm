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


class RunX(Worker):

    def __init__(self, project, api=None):
        super(RunX, self).__init__(api)
        self.project = project
        self.WD = os.path.abspath('.')

    def _locate_extension(self, name):
        exinfo = None
        # check for epm project local
        if self.project.metainfo:
            meta = self.project.get('extension') or {}
            if name in meta:
                exinfo = dict({'purpose': 'package',
                               'dir': os.path.join(self.project.dir, 'extension', name),
                               'defination': 'extension.yml',
                               '__origin__': 'package',
                               }, **meta)
                path = os.path.join(meta['dir'], meta['defination'])
                if not os.path.exists(path):
                    raise Exception("extension <{name}> defined in meta-info file, but implement not found {path}.")
        # find in workspace
        WORKBENCH = os.environ.get('EPM_WORKBENCH')
        if not exinfo and WORKBENCH:
            directory = os.path.expanduser(f'~/.epm/.workbench/{WORKBENCH}/extension/{name}')
            path = f"{directory}/extension.yml"
            if os.path.exists(path):
                exinfo = {'purpose': 'general',
                          'dir': directory,
                          'defination': 'extension.yml',
                          '__origin__': 'workbench',
                          }
        if not exinfo:
            directory = os.path.expanduser(f'~/.epm/extension/{name}')
            path = f"{directory}/extension.yml"
            if os.path.exists(path):
                exinfo = {'purpose': 'general',
                          'dir': directory,
                          'defination': 'extension.yml',
                          '__origin__': 'global',
                          }
        return exinfo


    def exec(self, command, runner=None, argv=[]):

        m = self.project.metainfo
        script = m.get('script', {}).get(command)
        if not script:
            raise ModuleNotFoundError('no <{}> in script'.format(command))

        cmdline = script
        if isinstance(script, dict):
            location = script.get('location')
            cmdline = script.get('command')
            path = os.path.normpath(os.path.join('.epm', 'script', command))
            if os.path.exists(path):
                shutil.rmtree(path)
            d = cache(location)
            shutil.copytree(d, path)
            cmdline = '%s/%s' % (path, cmdline)

        cmdline = cmdline.strip()
        args = cmdline.split(' ', 1)
        filename = args[0]
        command = []

        if len(args) > 1:
            import shlex

            for i in shlex.split(args[1]):
                if ' ' in i:
                    i = '"{}"'.format(i)

                command.append(i)

        command = [filename] + command

        if filename.endswith('.py'):
            command = [sys.executable] + command

        profile = self.project.profile.name if self.project.profile else None
        scheme = self.project.scheme.name if self.project.scheme else None

        env_vars = {'EPM_SANDBOX_PROFILE': profile,
                    'EPM_SANDBOX_SCHEME': scheme,
                    'EPM_SANDBOX_RUNNER': runner
                    }

        from conans.tools import environment_append
        with environment_append(env_vars):
            return Runner(self, 'shell').exec(command, argv)