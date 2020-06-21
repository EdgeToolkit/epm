import sys
import os
import yaml
import re
import stat
import fnmatch
import pathlib
from pathlib import PurePath
from string import Template
from jinja2 import PackageLoader, Environment, FileSystemLoader

from epm.errors import EException, ENotFoundError


from epm.util.files import mkdir

from epm.util import system_info, is_elf, sempath
from epm.enums import Platform, Architecture

from conans.client.generators.text import TXTGenerator
from conans.util.files import load
from conans.model.info import ConanInfo
from epm.paths import DATA_DIR

PLATFORM, ARCH = system_info()


# http://www.pixelbeat.org/programming/linux_binary_compatibility.html

def conanbuildinfo(folder):
    path = os.path.join(os.path.join(folder, 'conanbuildinfo.txt'))
    if os.path.exists(path):
        cpp, _, _ = TXTGenerator.loads(load(path))
        return cpp
    return None


#def conaninfo(folder):
#    return ConanInfo.load_from_package(folder)
#
#
#P_PATH = re.compile(r'(?P<folder>(build|package))/(?P<relpath>\S+)')
#P_PREFIX = re.compile(r'(?P<prefix>\.test/[\w\-\.]+)/(?P<path>\S+)')
#P_PATH = re.compile(r'(?P<prefix>[\w\-\.]+)?/(?P<folder>(build|package))/(?P<relpath>\S+)')

HOST_FOLDER = '@host'
PROJECT_FOLDER = '%s/project' % HOST_FOLDER
CONAN_STORAGE = '%s/conan.storage' % HOST_FOLDER
SANDBOX_FOLDER = '%s/.sandbox' % HOST_FOLDER


class Program(object):

    def __init__(self, project, sandbox, build_folder, storage=None):
        self._project = project
        self._sandbox = sandbox
        self._build_folder = build_folder
        filename = os.path.join(self._build_folder,
                                self._sandbox.folder or '',
                                self._sandbox.program)
        print(filename)

        if not self._is_program(filename):
            raise Exception('Can not find sandbox program %s in %s' %
                            (self._sandbox.program, self._build_folder))
        self._filename = pathlib.PurePath(os.path.abspath(filename)).as_posix()
        self._argv = sandbox.argv
        self._wd = pathlib.PurePath(os.path.abspath('.')).as_posix()
        self._storage_path = storage or os.getenv('CONAN_STORAGE_PATH') or self._project.api.conan_storage_path

    def _sempath(self, path, prefixes=None, check=False):
        prefixes = prefixes or ['project={}'.format(self._wd), 'storage={}'.format(self._storage_path)]
        result = sempath(path, prefixes)
        if check and not result:
            raise Exception('{} can not located in {}'.format(path, str(prefixes)))
        return result

    @property
    def storage_path(self):
        return self._storage_path

    @property
    def _ext(self):
        return '.exe' if self._is_windows else ''

    @property
    def _is_windows(self):
        return self._project.profile.settings['os'] == Platform.WINDOWS

    @property
    def _is_linux(self):
        return self._project.profile.settings['os'] == Platform.LINUX

    def _is_program(self, path):
        filename = path + self._ext
        if os.path.exists(filename):
            if os.path.isfile(filename):
                return filename
            elif os.path.islink(filename):
                real = os.path.realpath(filename)
                if os.path.isfile(real):
                    return filename
        return None

    def _template(self, filename):
        path = os.path.join(DATA_DIR, 'sandbox')
        env = Environment(loader=FileSystemLoader(path))
        env.trim_blocks = True
        template_file = os.path.basename(filename)
        template = env.get_template(template_file)
        return template

    @property
    def libdirs(self):
        dirs = []
        cpp = conanbuildinfo(self._build_folder)
        libdirs = cpp.bindirs if self._is_windows else cpp.libdirs
        for i in libdirs:
            dirs.append(i)

        return [PurePath(x).as_posix() for x in dirs]

    @property
    def dynamic_libs(self):
        libs = {}
        for libd in self.libdirs:
            if not os.path.exists(libd):
                continue

            for name in os.listdir(libd):
                filename = os.path.join(libd, name)
                if os.path.isdir(filename):
                    continue

                symbol = False

                if self._is_windows and fnmatch.fnmatch(name, "*.dll"):
                    target = self._sempath(filename)
                    assert target, 'Failed local %s' % filename

                elif self._is_linux and (fnmatch.fnmatch(name, '*.so')
                                         or fnmatch.fnmatch(name, '*.so.*')):

                    path = filename
                    if os.path.islink(filename):
                        symbol = True
                        path = os.readlink(filename)

                        if not os.path.isabs(path):
                            path = os.path.join(libd, path)
                    target = self._sempath(path)
                    assert target, 'Failed local %s -> %s' % (filename, path)

                else:
                    continue
                libs[name] = {'target': target, 'symbol': symbol, 'origin': filename, 'host': PLATFORM}
        return libs

    @property
    def _docker_image(self):
        docker = self._project.profile.docker.runner
        if not docker:
            raise EException('{} no docker for runner'.format(self._project.name))
        return docker.get('image')

    @property
    def _docker_shell(self):
        docker = self._project.profile.docker.runner
        if not docker:
            raise EException('{} no docker for runner'.format(self._project.name))
        return docker.get('shell', '/bin/bash')

    def _windows(self, name):
        def _(path):
            spath = self._sempath(path, check=True)
            s = Template(spath).substitute(storage=r'%EPM_SANDBOX_STORAGE%',
                                           project=r'%EPM_SANDBOX_PROJECT%')
            return str(pathlib.PureWindowsPath(s))

        filename = _(self._filename)

        libdirs = [_(x) for x in self.libdirs]

        template = self._template('windows.j2')
        return template.render(name=name,
                               package_name=self._project.name,
                               sandbox=self._sandbox,
                               libdirs=libdirs,
                               filename=filename,
                               folder=self._project.folder,
                               profile=self._project.profile,
                               scheme=self._project.scheme,
                               arguments=" ".join(self._argv))

    def _linux(self, name):
        # libdirs = []

        filename = self._sempath(self._filename)

        template = self._template('linux.j2')
        docker = self._project.profile.docker.runner or {}
        docker = dict({'image': 'alpine', 'shell': '/bin/bash', 'home': '/tmp'}, **docker)

        return template.render(name=name,
                               package_name=self._project.name,
                               sandbox=self._sandbox,
                               filename=filename,
                               dylibs=self.dynamic_libs,
                               #image=docker['image'],
                               #shell=docker['shell'],
                               #home=docker['home'],
                               docker=docker,
                               folder=self._project.folder,
                               profile=self._project.profile,
                               scheme=self._project.scheme,
                               arguments=" ".join(self._argv))

    def _linux_windows_docker(self, name):
        def _(path):
            s = Template(path).substitute(storage=r'$EPM_SANDBOX_STORAGE',
                                          project=r'$EPM_SANDBOX_PROJECT',
                                          folder=self._project.folder,
                                          profile=self._project.profile,
                                          scheme=self._project.scheme
                                          )
            return PurePath(s).as_posix()

        template = self._template('linux.cmd.j2')

        docker = self._project.profile.docker.runner or {}
        docker = dict({'image': 'alpine', 'shell': '/bin/bash', 'home': '/tmp'}, **docker)

        return template.render(name=name,
                               package_name=self._project.name,
                               sandbox=self._sandbox,
                               docker=docker,
                               folder=self._project.folder,
                               profile=self._project.profile,
                               scheme=self._project.scheme,
                               arguments=" ".join(self._argv))

    def generate(self, name):

        if not self._filename:
            print('WARN: can not find <%s>, skip generate sandbox.' % self._path)
            return

        filename = os.path.join(self._project.folder.out, 'sandbox', name)
        mkdir(os.path.dirname(filename))

        if self._is_windows:
            script = self._windows(name).encode('utf-8')
            with open(filename + '.cmd', 'wb') as f:
                f.write(script)
        else:
            script = self._linux(name).encode('utf-8')
            with open(filename, 'wb') as f:
                f.write(script)
            #    f.close()
            mode = os.stat(filename).st_mode
            os.chmod(filename, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            script = self._linux_windows_docker(name).encode('utf-8')
            with open(filename + '.cmd', 'wb') as f:
                f.write(script)
