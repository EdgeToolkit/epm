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


def conaninfo(folder):
    return ConanInfo.load_from_package(folder)


P_PATH = re.compile(r'(?P<folder>(build|package))/(?P<relpath>\S+)')
P_PREFIX = re.compile(r'(?P<prefix>\.test/[\w\-\.]+)/(?P<path>\S+)')
P_PATH = re.compile(r'(?P<prefix>[\w\-\.]+)?/(?P<folder>(build|package))/(?P<relpath>\S+)')

HOST_FOLDER = '@host'
PROJECT_FOLDER = '%s/project' % HOST_FOLDER
CONAN_STORAGE = '%s/conan.storage' % HOST_FOLDER
SANDBOX_FOLDER = '%s/.sandbox' % HOST_FOLDER

# Join two (or more) paths.
def join(path, *paths):
    path = os.path.join(path, *paths)
    path = os.path.normpath(path)
    path = path.replace('\\', '/')
    return path


class Program(object):

    def __init__(self, project, commandline, storage, is_create=False, id=None):
        self._project = project

        self._commandline = commandline
        argv = commandline.split(' ')
        self._path = argv[0]
        self._argv = argv[1:]
        self._prefix = ''
        path = self._path

        m = P_PATH.match(path)
        self._prefix = m.group('prefix')
        self._folder = m.group('folder')
        self._relpath = m.group('relpath')
        self._middle = " ".join(self._relpath.split('/')[:-1])
        self._name = os.path.basename(self._path)
        self._fullname = self._name + self._ext

        self._storage_path = pathlib.PurePath(os.path.abspath(storage)).as_posix()
        self._is_create = is_create
        self._id = id

        self._wd = pathlib.PurePath(os.path.abspath('.')).as_posix()
        self._build_dir = None

        self._initialize()

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

    def _initialize(self):

        if self._is_create and not self._prefix:
            self._filename, self._build_dir = self._locate('conan')
        else:
            self._filename, self._build_dir = self._locate('project')

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

    def _locate(self, where='project'):
        project = self._project

        def ppath(m):
            folder = join(project.folder.out, self._prefix, self._folder)
            return join(folder, m, self._name), folder

        def cpath(m, storage=None):
            rpath = project.reference.dir_repr()
            storage = storage or self.storage_path
            folder = join(storage, rpath, self._folder, self.id)
            return join(folder, m, self._name), folder
        folders = ['bin'] if self._folder == 'package' else ['bin', '']
        folders = [self._middle] if self._middle else folders
        for m in folders:
            if where == 'project':
                path, folder = ppath(m)
                if self._is_program(path):
                    return os.path.abspath(path), folder
            else:
                path, folder = cpath(m)
                if self._is_program(path):
                    return os.path.abspath(path), folder

        raise ENotFoundError('can not locate program <{}> in {}'.format(self._name, where))

    @property
    def id(self):
        return self._id

    @property
    def libpath(self):
        dirs = []
        project = self._project
        storage = self.storage_path
        outdir = os.path.abspath(project.folder.out)
        sub_folder = 'bin' if self._is_windows else 'lib'

        # build artifacts
        if self._is_create:
            rpath = project.reference.dir_repr()
            path = join(storage, rpath, self._folder , self.id, sub_folder)
            dirs.append(path)
        else:
            root = os.path.join(outdir, self._folder)
            libd = os.path.join(root, sub_folder)
            for i in [libd, root]:
                dirs.append(i)


        # dependencies
        # build command will use editable info which saved in conanbuildinfo.txt
        # create command use conaninfo.txt

        if self._is_create and self._folder in ['package']:
            info = conaninfo(self._build_dir)

            for i in info.full_requires:
                from conans.model.ref import ConanFileReference
                ref = ConanFileReference.loads(i.full_str(), False)
                print('--- ref:', ref)
                print('--- ref.dir_repr():', ref.dir_repr())
                dirs.append(ref.dir_repr())
        else:
            cpp = conanbuildinfo(self._build_dir)
            libdirs = cpp.bindirs if self._is_windows else cpp.libdirs
            for i in libdirs:
                dirs.append(i)

        return [PurePath(x).as_posix() for x in dirs]

    @property
    def dynamic_libs(self):
        libs = {}
        for libd in self.libpath:
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

        libdirs = [_(x) for x in self.libpath]

        template = self._template('windows.j2')
        return template.render(name=name,
                               libdirs=libdirs,
                               filename=filename,
                               folder=self._project.folder,
                               profile=self._project.profile,
                               scheme=self._project.scheme,
                               arguments=" ".join(self._argv))

    def _linux(self, name):
        #libdirs = []

        filename = self._filename

        template = self._template('linux.j2')
        docker = self._project.profile.docker.runner or {}
        docker = dict({'image': 'alpine', 'shell': '/bin/bash', 'home': '/tmp'}, **docker)

        return template.render(name=name,
                               #libdirs=libdirs,
                               filename=filename,
                               dylibs=self.dynamic_libs,
                               #docker=docker,
                               image=docker['image'],
                               shell=docker['shell'],
                               home=docker['home'],
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

#        filename = _(self._filename)

#        libdirs = [_(x) for x in self.libpath]

        template = self._template('linux.cmd.j2')
        
        docker = self._project.profile.docker.runner or {}
        docker = dict({'image': 'alpine', 'shell': '/bin/bash', 'home': '/tmp'}, **docker)

        return template.render(name=name,
                               #filename=filename,
                               #libdirs=libdirs,
                               #dylibs=self.dynamic_libs,
                               docker=docker,
                               #image=docker['image'],
                               #shell=docker['shell'],
                               #home=docker['home'],
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











