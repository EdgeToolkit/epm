
import os
import glob
import shutil
from conans.model.ref import ConanFileReference, PackageReference
from conans.client.tools import environment_append
from conans.tools import chdir, load, mkdir, rmdir
from conans.model.info import ConanInfo
from conans.paths import CONANINFO


from epm import HOME_DIR
from epm.worker import Worker
from epm.errors import EConanException
from epm.worker.sandbox import build_tests, Generator
from epm.utils.docker import BuildDocker
from epm.utils import PLATFORM

from epm.model.program import ProgramX as Program


def conandir(path):
    """ conan short path probe

    :param path:
    :return:
    """
    if PLATFORM == 'Windows':
        link = os.path.join(path, '.conan_link')
        if os.path.exists(link):
            from conans.util.files import load
            path = load(link)
    return path


def _del(path):
    if os.path.isdir(path):
        rmdir(conandir(path))
    else:
        os.remove(path)


def _clear_folder(path):
    if not os.path.isdir(path):
        return
    with chdir(path):
        for i in os.listdir('.'):
            _del(i)

def _dep_graph(storage_path, full_requires, result={}):
    for package in full_requires:
        print('+', package, package.ref, package.ref.dir_repr())
        pkg_dir = os.path.join(storage_path, package.ref.dir_repr(), 'package', package.id)
        info_path = os.path.join(pkg_dir, CONANINFO)
        conan_info = ConanInfo.load_file(info_path)
        result[str(package)] = package
        _dep_graph(storage_path, conan_info.full_requires, result)
    
    return result

class Creator(Worker):

    def __init__(self, api=None):
        super(Creator, self).__init__(api)

    def exec(self, param):
        project = self.api.project(param['PROFILE'], param.get('SCHEME'))
        runner = param.get('RUNNER') or os.getenv('EPM_RUNNER') or 'auto'
        clear = param.get('clear', False)
        storage = param.get('storage', None)
        archive = param.get('archive', None)
        with_deps = param.get('with_deps') or False
        program = param['program']
        if not project.available:
            raise Exception("unavailble configure")

        if runner == 'auto':
            runner = 'docker' if project.profile.docker.builder else 'shell'
        
        if runner == 'docker':
            docker = BuildDocker(project)

            command = f"epm --runner shell --profile {project.profile.name}"
            if project.scheme and project.scheme.name:
                command += f" --scheme {project.scheme.name}"
            command += f" create"
            docker.environment['EPM_RUNNING_SYSTEM'] = 'docker'
            docker.environment['EPM_RUNNER'] = 'shell'

            if storage:
                docker.environment['CONAN_STORAGE_PATH'] = '%s/%s' % (docker.cwd, storage)
                command += f" --storage {storage}"
            if archive:
                command += f" --archive {archive}"
            if with_deps:
                command += f" --with-deps"
            if program:
                command += f" --program {program}"
    
            proc = docker.run(command)
            if proc.returncode:
                raise Exception(f"[Docker] {command} failed.")

        else:
            storage_path = os.path.join(project.dir, storage, 'data') if storage else self.api.conan_storage_path
            env_vars = {'CONAN_STORAGE_PATH': storage_path}
            if PLATFORM == 'Windows' and storage:
                short_home = os.path.join(project.dir, storage, 'short')
                env_vars['CONAN_USER_HOME_SHORT'] = short_home

            if storage:
                rmdir(os.path.join(project.dir, storage))

            with environment_append(dict(self.api.config.env_vars, **env_vars)):
                self._exec(project, program)

            if archive:
                self._archive(project, archive, storage_path)
                if with_deps:
                    self._archive_deps(project, archive, storage_path)

            if clear:
                self._clear(project)
    
    def _build_package(self, project):
        conan = self.api.conan
        scheme = project.scheme

        project.setup()
        path = project.abspath
        for i in conan.editable_list():
            conan.editable_remove(i)
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
                 
    def _exec(self, project, program=None):
        if program is None or program == 'disable':
            self._build_package(project)
        if project.profile.host.settings['os'] == 'iOS':
            self.out.info("skip program building, NOT support in iOS for now :-).")
            return
        
        if program != 'disable' and project.profile.host:
            
            built = set()
            for name, test in project.test.items():
                if test.project and test.project not in built:                    
                    program = Program(project, name)
                    program.build()
                    built.add(test.project)
                    
            for name, test in project.test.items():
                program.generate()
  
    def _archive(self, project, path, storage_path):
        ref = project.reference
        pacage_id = project.record.get('package_id')
        rootpath = os.path.join(storage_path, ref.dir_repr())
        pkg_dir = os.path.join(rootpath, 'package', pacage_id)

        # package
        root = os.path.join(path, ref.dir_repr())
        rmdir(root)
        mkdir(f"{root}/package")
        mkdir(f"{root}/export_source")
        shutil.copyfile(f"{rootpath}/metadata.json", f"{root}/metadata.json")
        _ = conandir
        shutil.copytree(_(pkg_dir), f"{root}/package/{pacage_id}")
        shutil.copytree(_(f"{rootpath}/export"), f"{root}/export")

    def _archive_deps(self, project, path, storage_path):
        ref = project.reference
        pacage_id = project.record.get('package_id')
        rootpath = os.path.join(storage_path, ref.dir_repr())
        pkg_dir = os.path.join(rootpath, 'package', pacage_id)
        info_path = os.path.join(pkg_dir, CONANINFO)
        conan_info = ConanInfo.load_file(info_path)
        deps = _dep_graph(storage_path, conan_info.full_requires)
        for pkg in deps.values():            
            folder = os.path.join(pkg.ref.dir_repr(), 'package', pkg.id)
            src = os.path.join(storage_path, folder)
            dest = os.path.join(path, folder)
            rmdir(dest)
            mkdir(os.path.abspath(f"{dest}/.."))
            shutil.copytree(src, dest)
            
    def _clear(self, project):
        from conans.tools import chdir
        program_dir = os.path.join(project.abspath.out, 'program')
        if os.path.isdir(program_dir):
            for name in os.listdir(program_dir):
                for i in os.listdir(os.path.join(program_dir, name)):
                    if i not in ['bin', 'lib']:
                        _del(os.path.join(program_dir, name, i))
            
        
