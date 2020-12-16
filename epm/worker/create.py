
import os
import glob
import shutil
from conans.model.ref import ConanFileReference
from conans.client.tools import environment_append
from conans.tools import chdir, load, mkdir, rmdir

from epm import HOME_DIR
from epm.worker import Worker, DockerBase, param_encode
from epm.errors import EConanException, EDockerException
from epm.worker.sandbox import build_tests, Generator

from epm.utils import PLATFORM

def conan_real_path(path):
    from conans.util.windows import CONAN_LINK
    link = os.path.join(path, CONAN_LINK)
    if os.path.exists(link):
        return load(link)
    return path

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
        archive = param.get('archive', None)

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

            storage_path = os.path.join(project.dir, storage, 'data') if storage else self.api.conan_storage_path
            env_vars = {'CONAN_STORAGE_PATH': storage_path}
            if PLATFORM == 'Windows' and storage:
                short_home = os.path.join(project.dir, storage, 'short')
                env_vars['CONAN_USER_HOME_SHORT'] = short_home

            if storage:
                rmdir(os.path.join(project.dir, storage))

            with environment_append(dict(self.api.config.env_vars, **env_vars)):
                self._exec(project)
                build_tests(project)
                Generator.build(project, True)

            if archive:
                rmdir(archive)
                self._archive(project, archive, storage_path)

            if clear:
                clearer = Cleaner(project, storage)
                clearer.clear(storage=bool(storage))

    def _exec(self, project):

        conan = self.api.conan
        scheme = project.scheme

        project.setup()
        path = project.abspath

        for i in conan.editable_list():
            conan.editable_remove(i)
        try:
            del os.environ['MESON_CROSS_FILE']
        except:
            pass
        if os.path.exists(path.cross_file):
            os.environ['MESON_CROSS_FILE'] = path.cross_file

        info = self.conan.create(project.dir,
                                 name=project.name,
                                 version=project.version,
                                 user=project.user,
                                 channel=project.channel,
                                 settings=None,
                                 options=scheme.as_list(),
                                 profile_names=[path.profile_host],
                                 profile_build=project.profile.build,
                                 test_folder=False)
                         
        if info['error']:
            raise EConanException('create package failed.', info)

        id = info.get('installed')[0].get('packages')[0]['id']
        result = {'id': id}
        project.record.set('package_id', id)
        return result

    def _archive(self, project, path, storage_path):
        ref = project.reference
        pacage_id = project.record.get('package_id')
        rootpath = os.path.join(storage_path, ref.dir_repr())
        pkg_dir = os.path.join(rootpath, 'package', pacage_id)

        # package
        root = os.path.join(path, ref.dir_repr())
        mkdir(root)
        shutil.copyfile(f"{rootpath}/metadata.json", f"{root}/metadata.json")

        mkdir(f"{root}/package")
        mkdir(f"{root}/export_source")
        from epm.utils import conandir as _

        shutil.copytree(_(pkg_dir), f"{root}/package/{pacage_id}")
        shutil.copytree(_(f"{rootpath}/export"), f"{root}/export")


def _del(path):
    if os.path.isdir(path):
        from epm.utils import conandir as _
        rmdir(_(path))
    else:
        os.remove(path)


def _clear_folder(path):
    if not os.path.isdir(path):
        return
    with chdir(path):
        for i in os.listdir('.'):
            _del(i)


class Cleaner(object):

    def __init__(self, project, storage=None):
        self._project = project
        self._api = project.api
        self._ref = ConanFileReference(project.name, project.version, project.user, project.channel, validate=False)
        self._storage = storage
        self._conaninfo = None
        self._rootpath = None

    @property
    def storage_path(self):
        return os.path.join(self._project.dir, self._storage, 'data') if self._storage else None

    @property
    def short_path(self):
        if PLATFORM == 'Windows' and self._storage:
            return os.path.join(self._project.dir, self._storage, 'short')
        return None

    @property
    def rootpath(self):
        if self._rootpath is None:
            self._rootpath = os.path.join(self.storage_path, self._ref.dir_repr())
        return self._rootpath

    def clear(self, cache=True, storage=False):
        if cache:
            self._clear_cache()
        if storage:
            self._clear_storage()

    def _clear_cache(self):

        with chdir(self._project.abspath.out):
            for i in os.listdir("."):
                if i in ['sandbox', 'test', 'record.yaml']:
                    pass
                else:
                    _del(i)
        test_path = f"{self._project.abspath.out}/test"
        if os.path.isdir(test_path):
            with chdir(test_path):
                for i in glob.glob("*/*"):
                    name = os.path.basename(i)
                    if name in ['lib', 'bin', 'conanbuildinfo.txt', 'conaninfo.txt', 'graph_info.json']:
                        pass
                    else:
                        _del(i)

    def _clear_storage(self):
        if not self._storage:
            return
        with chdir(self.rootpath):
            for i in os.listdir("."):
                if i in ['export', 'export_source', 'package', 'metadata.json']:
                    pass
                else:
                    _del(i)
            _clear_folder('export_source')
