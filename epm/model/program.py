import os
import glob
import pathlib
import subprocess
import stat
from conans.tools import chdir
from epm.utils.logger import syslog
from epm.utils import PLATFORM, ARCH

class Program(object):

    def __init__(self, project, name):
        self._project = project
        self._config = project.test[name]
        
    @property
    def name(self):
        return self._config.name    
   
    @property
    def source_dir(self):
        return self._config.project
    
    @property
    def filename(self):
        ext = ".exe" if self._is_win else ''
        return f"{self._config.program}{ext}"

    @property
    def storage_path(self):
        return os.getenv('CONAN_STORAGE_PATH') or self._project.api.conan_storage_path

    @property
    def _is_win(self):
        return self._project.profile.host.settings['os'] == 'Windows'


    @property
    def _patterns(self):
        return self._config.pattern or ['bin', '']

    def _find(self, folder, root):
        storage = self.storage_path if root == 'storage' else self._project.dir
        
        directory = os.path.join(storage, folder)
        if os.path.exists(directory):
            with chdir(directory):
                for pattern in self._patterns:
                    path = glob.glob(f"{pattern}/{self.filename}")
                    syslog.info(f'find program executable {self.filename} in <{root}>:{storage}' +
                                "\nroot: {}".format(os.path.abspath('.')) +
                                "\npattern: {}".format(pattern) +
                                "\n {} found. {}".format(len(path), "\n".join(path)))    
                    if path:
                        return path[0]
        return None

    def generate(self):
        if not self._config.program:
            message = project.api.out.info
            message(f"-- skip generate for {self.name} as it has no executable program.")
            return
        project = self._project
        config = self._config
        builtin = config.project is None
        package_id = project.record.get('package_id')
        folder = None
        where = 'storage'
        if builtin:
            build_folder = os.path.join(project.reference.dir_repr(), 'build', package_id)
            package_folder = os.path.join(project.reference.dir_repr(), 'package', package_id)
            for i in [package_folder, build_folder]:
                path = self._find(i, where)
                if path:
                    folder = i
                    break
        else:
            where = 'project'
            build_folder = os.path.join(project.path.program, self._config.project)
            path = self._find(build_folder, where)
            
            if path:
                folder = build_folder

        if not path or not folder:
            raise FileNotFoundError(f'can not find {self._config.project} in {where}.')

        rootpath = os.path.join(self.storage_path if where == 'storage' else project.dir)
        conaninfo_path = os.path.join(rootpath, folder, 'conaninfo.txt')
        from conans.model.info import ConanInfo
        from conans.util.files import load, mkdir
        conaninfo = ConanInfo.loads(load(conaninfo_path))
        libs, deps = self._parse_dynamic_libs(conaninfo)
        libdirs = set([os.path.dirname(x) for x in libs])
        depdirs = set([os.path.dirname(x) for x in deps])
        from collections import namedtuple
        context = {'libs': libs, 'deps': deps, 'package_id': package_id or '',
                   'dirs': namedtuple('D', 'lib, dep')(libdirs, depdirs),
                   'project': project, 'program': self, 'config': self._config,
                   'filename': path, 'where': where,
                   'command': 'create' if package_id else 'build'
                   }
        self._render(context)

    def _render(self, context):
        from epm.utils import Jinja2
        from epm import DATA_DIR
        out_dir = os.path.join(self._project.abspath.out, 'sandbox')
        j2 = Jinja2(directory=f"{DATA_DIR}/program", context=context)

        if self._is_win:
            j2.render("windows.cmd.j2", outfile=f"{out_dir}/{self.name}.cmd")
        else:
            j2.render("linux.sh.j2", outfile=f"{out_dir}/{self.name}")
            j2.render("linux.cmd.j2", outfile=f"{out_dir}/{self.name}.cmd")
            os.chmod(f"{out_dir}/{self.name}", stat.S_IRWXU | stat.S_IXGRP | stat.S_IRGRP | stat.S_IROTH)

    def _parse_dynamic_libs(self, conaninfo):
        libs = []
        deps = []
        win = bool(conaninfo.settings.os == 'Windows')
        storage = self.storage_path
        if not os.path.exists(storage):
            return list(), list()

        with chdir(storage):
            for pref in conaninfo.full_requires:
                path = os.path.join(pref.ref.dir_repr(), 'package', pref.id)
                if win:
                    lib = glob.glob(f'{path}/bin/*.dll')
                    lib += glob.glob(f'{path}/bin/**/*.dll', recursive=True)
                else:
                    lib = glob.glob(f'{path}/lib/*.so')
                    lib += glob.glob(f'{path}/lib/*.so.*')
                    lib += glob.glob(f'{path}/lib/**/*.so', recursive=True)
                    lib += glob.glob(f'{path}/lib/**/*.so.*', recursive=True)

                if pref.ref.name == self._project.name:
                    libs += lib
                else:
                    deps += lib

        def _(x):
            return pathlib.WindowsPath(x) if win else pathlib.PosixPath(x)

        return [_(x) for x in libs], [_(x) for x in deps]
    
    def build(self):
        project = self._project
        if not self._config.project:
            project.api.out.warn(f"test progra {self._config.name} is a package built executable.")
            return None
        
        name = self._config.name
        

        project.api.out.highlight(f"\n==== build test program ({name})\n")

        build_folder = os.path.join(project.path.program, name)
        WD = os.path.join(project.dir, self._config.project)

        conan = project.api.conan
        scheme = project.scheme
        from conans.tools import environment_append

        with environment_append({'EPM_PROJECT_DIRECTORY': project.dir,
                                 'EPM_PROGRAM_NAME': name}):
            info = conan.install(WD,
                                 options=scheme.as_list(True),
                                 profile_names=[project.abspath.profile_host],
                                 install_folder=build_folder,
                                 profile_build=project.profile.build)
            if info['error']:
                raise Exception('configure program <{}> failed.'.format(self.location), info)

            conan.build(WD,
                        build_folder=build_folder,
                        install_folder=build_folder) 
            return info
