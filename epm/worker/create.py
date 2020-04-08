
import os
import glob
import fnmatch

from conans.client.tools import environment_append

from epm.worker import Worker, DockerBase, param_encode
from epm.model.project import Project
from epm.errors import APIError, EException
from epm.model.sandbox import Program
from epm.util import is_elf
from epm.util.files import remove, rmdir
from epm.paths import HOME_EPM_DIR

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
        project = Project(param['PROFILE'], param.get('SCHEME'), self.api)
        runner = param.get('RUNNER') or 'auto'
        clear = param.get('clear', False)
        storage = param.get('storage', None)

        if runner == 'auto':
            runner = 'docker' if project.profile.docker.builder else 'shell'

        try:
            if runner == 'shell':
                storage = os.path.join(project.dir, storage) if storage else self.api.conan_storage_path
                with environment_append(dict(self.api.config.env_vars,
                                             **{'CONAN_STORAGE_PATH': storage})):
                    self._exec(project, clear)
            elif runner == 'docker':
                param['RUNNER'] = 'shell'
                docker = Docker(self.api, project)
                docker.WD = '$home/project/%s' % project.name

                docker.add_volume(project.dir, docker.WD)
                docker.add_volume(HOME_EPM_DIR, '$home/.epm')
                if storage:
                    docker.environment['CONAN_STORAGE_PATH'] = '%s/%s' % (docker.WD, storage)
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
        profile = project.profile

        project.initialize()
        profile_path = os.path.join(project.folder.out, 'profile')
        profile.save(profile_path)

        options = ['%s=%s' % (k, v) for (k, v) in scheme.options.as_list()]

        for i in conan.editable_list():
            conan.editable_remove(i)

        info = self.conan.create('.',
                                 name=project.name,
                                 version=project.version,
                                 user=project.group,
                                 channel=project.channel,
                                 settings=None,
                                 options=options,
                                 profile_names=[profile_path],
                                 test_folder=False)

        if info['error']:
            raise APIError('failed when create package %s | %s '
                           % (project.name, scheme.name), details={})

        id = info.get('installed')[0].get('packages')[0]['id']

        result = {'id': id}
        dirs = None

        self._test(project)

        if clear:
            for i in glob.glob('%s/*/*' % project.folder.test):
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
        project.save({'package_id': id})
        if dirs:
            result['dirs'] = dirs

        return result

    def _test(self, project):
        conan = self.api.conan

        #profile_path = os.path.join(project.folder.out, 'profile')  # already generated in configure step

        options = ['%s=%s' % (k, v) for k, v in project.scheme.package_options.as_list()]
        tests = project.tests or []
        if not tests:
            if os.path.exists('tests/conanfile.py'):
                tests = ['tests']

        for i in tests:
            conanfile_path = os.path.join(i, 'conanfile.py')
            if not os.path.exists(conanfile_path):
                raise EException('specified test <%s> miss Makefile.py' % i)
            instd = os.path.join(project.folder.test, i, 'build')
            pkgdir = os.path.join(project.folder.test, i, 'package')

            info = conan.install(path=conanfile_path,
                                 name='%s-%s' % (project.name, i),
                                 settings=None,  # should be same as profile
                                 options=options,
                                 profile_names=[project.generate_profile()],
                                 install_folder=instd)

            info = conan.build(conanfile_path=conanfile_path,
                               package_folder=pkgdir,
                               build_folder=instd,
                               install_folder=instd)

            info = conan.package(path=conanfile_path,
                                 build_folder=instd,
                                 package_folder=pkgdir,
                                 install_folder=instd)

    def _sandbox(self, project, id):
        storage = os.environ.get('CONAN_STORAGE_PATH')
        for name, command in project.manifest.get('sandbox', {}).items():
            program = Program(project, command, storage, is_create=True, id=id)
            program.generate(name)
