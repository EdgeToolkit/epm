
import os
import glob
import fnmatch

from conans.util.files import remove, rmdir
from conans.client.tools import environment_append
from conans.errors import ConanException

from epm import HOME_DIR
from epm.worker import Worker, DockerBase, param_encode
from epm.errors import EException, EConanException, EDockerException
from epm.utils import is_elf




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
        project = self.api.project(param['PROFILE'], param.get('SCHEME'))
        runner = param.get('RUNNER') or 'auto'
        clear = param.get('clear', False)
        storage = param.get('storage', None)

        if runner == 'auto':
            runner = 'docker' if project.profile.docker.builder else 'shell'

        if runner == 'docker':
            param['RUNNER'] = 'shell'
            docker = Docker(self.api, project)
            docker.WD = '$home/project/%s' % project.name

            docker.add_volume(project.dir, docker.WD)
            docker.add_volume(HOME_DIR, '$home/.epm')
            if storage:
                docker.environment['CONAN_STORAGE_PATH'] = '%s/%s' % (docker.WD, storage)
            docker.exec('epm api create %s' % param_encode(param))
            if docker.returncode:
                raise EDockerException(docker)

        else:
            storage = os.path.join(project.dir, storage) if storage else self.api.conan_storage_path
            with environment_append(dict(self.api.config.env_vars,
                                         **{'CONAN_STORAGE_PATH': storage})):

                try:
                    self._exec(project, clear, bool(param.get('sandbox')))
                except ConanException as e:
                    raise EConanException('conan error in create', e)
                except EException as e:
                    raise e
                except BaseException as e:
                    raise EException('execute build api failure.', exception=e)

    def _exec(self, project, clear=False, sandbox=True):

        conan = self.api.conan
        scheme = project.scheme
        profile = project.profile

        project.initialize()

        filename = os.path.join(project.dir, project.folder.out, 'profile')
        profile.save(filename)

        options = ['%s=%s' % (k, v) for k, v in scheme.options.items()]
        for pkg, opts in scheme.reqs_options.items():
            options += ['%s:%s=%s' % (pkg, k, v) for k, v in opts.items())]



        for i in conan.editable_list():
            conan.editable_remove(i)

        info = self.conan.create(project.dir,
                                 name=project.name,
                                 version=project.version,
                                 user=project.user,
                                 channel=project.channel,
                                 settings=None,
                                 options=scheme.as_list(),
                                 profile_names=[filename],
                                 test_folder=False)
        if info['error']:
            raise EConanException('create package failed.', info)

        id = info.get('installed')[0].get('packages')[0]['id']
        project.record.set('package_id', id)

        result = {'id': id}
        dirs = None
        project.record.set('package_id', id)

        if sandbox:
            from epm.worker.sandbox import Builder as SB
            sb = SB(project, is_create_method=True)
            sb.exec()

        if clear:
            self._clear(project)

        if dirs:
            result['dirs'] = dirs

        return result

    def _clear(self, project):
        for i in glob.glob('%s/*/*' % project.folder.test):
            _clear_builds(i)
        _clear_storage(self.api.conan_storage_path, project.reference.dir_repr())

