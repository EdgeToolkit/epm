
import os
import glob
import fnmatch

from conans.client.tools import environment_append

from epm.worker import Worker, DockerBase, param_encode
from epm.model.project import Project
from epm.errors import APIError
from epm.model.sandbox import Program
from epm.util import is_elf
from epm.util.files import remove, rmdir


def _delete(path):
    if os.path.isfile(path):
        remove(path)
    elif os.path.isdir(path):
        rmdir(path)


def _clear(folder):
    for i in glob.glob('%s/*' % folder):
        _delete(i)


def _clear_builds(path):
    def clear(path):
        name = os.path.basename(path)
        ext = os.path.splitext(name)[-1]
        if name in ['conanbuildinfo.txt', 'conaninfo.txt']:
            pass
        elif ext in ['.exe', '.so', '.dll']:
            pass
        elif fnmatch.fnmatch(ext, '.so.*'):
            pass
        elif os.path.islink(path):
            pass
        elif os.path.isfile(path) and is_elf(path):
            pass
        else:
            _delete(path)

    for p in glob.glob('%s/*' % path):
        n = os.path.basename(p)
        if n in ['bin', 'lib']:
            for l in glob.glob('%s/*' % p):
                clear(l)
        else:
            clear(p)


def _clear_storage(storage, ref_path):
    base = '%s/%s' % (storage, ref_path)
    for i in glob.glob('%s/*' % base):
        name = os.path.basename(i)
        if name in ['package', 'metadata.json', 'export']:
            continue

        if name == 'build':
            for l in glob.glob('%s/*' % i):
                _clear_builds(l)
        elif name == 'export_source':
            _clear(i)
        else:
            _delete(i)


class Docker(DockerBase):

    def __init__(self, api, project):
        super(Docker, self).__init__(api, project)


class Creator(Worker):

    def __init__(self, api=None):
        super(Creator, self).__init__(api)

    def exec(self, param):
        project = Project(param['scheme'], self.api)
        scheme = project.scheme
        runner = param.get('runner') or 'auto'
        clear = param.get('clear', False)
        storage = param.get('storage', None)

        if runner == 'auto':
            runner = 'docker' if scheme.profile.docker.runner else 'shell'

        try:
            if runner == 'shell':
                storage = os.path.join(project.dir, storage) if storage else self.api.conan_storage_path
                with environment_append({'CONAN_STORAGE_PATH': storage}):
                    self._exec(project, clear)
            elif runner == 'docker':
                param['runner'] = 'shell'
                docker = Docker(self.api, project)
                docker.WD = '$home/project/%s' % project.name

                docker.add_volume(project.dir, docker.WD)
                docker.add_volume(self.api.cache_folder, '$home/host/.epm')
                if storage:
                    docker.environment['CONAN_STORAGE_PATH'] = '%s/%s' % (docker.WD, storage)

                docker.environment['EPM_USER_HOME'] = '$home/host/'

                docker.exec('epm api create %s' % param_encode(param))

            else:
                assert(False)
        except APIError:
            raise
        except BaseException as e:
            raise APIError('other error ', details={
                'info': e
            })

    def _exec(self, project, clear=False):
        conan = self.api.conan
        scheme = project.scheme

        project.initialize()
        profile_path = os.path.join(project.folder.out, 'profile')
        scheme.profile.save(profile_path)

        options = ['%s=%s' % (k, v) for (k, v) in scheme.options.as_list()]

        for i in conan.editable_list():
            conan.editable_remove(i)

        info = self.conan.create('.',
                                 name=project.name,
                                 version=project.version,
                                 user=project.user,
                                 channel=project.channel,
                                 settings=None,
                                 options=options,
                                 profile_names=[profile_path],
                                 test_build_folder=project.folder.test)
        if info['error']:
            raise APIError('failed when create package %s | %s '
                           % (project.name, scheme.name), details={})

        id = info.get('installed')[0].get('packages')[0]['id']
        result = {'id': id}
        dirs = None

        if clear:
            for i in glob.glob(project.folder.test):
                _clear_builds(i)
            _clear_storage(self.api.conan_storage_path, project.reference.replace('@', '/'))

            def sizeof(folder):
                size = 0
                for root, dirs, files in os.walk(folder):
                    for name in files:
                        path = os.path.join(root, name)
                        if os.path.isfile(path):
                            try:
                                size += os.path.getsize(path)
                            except:
                                pass
                return size
            dirs = {'.epm': {'size': sizeof('.epm')},
                    '$storage': {'size': sizeof(self.api.conan_storage_path)}
                    }

        self._sandbox(project, id=id)
        if dirs:
            result['dirs'] = dirs
        return result

    def _sandbox(self, project, id):
        storage = os.environ.get('CONAN_STORAGE_PATH')

        for folder in ['build', 'package', 'test_package']:
            for name, command in project.manifest.get('sandbox', {}).items():
                if command.startswith(folder):
                    program = Program(project, command, storage, is_create=True, id=id)

                    program.generate(name)
