import sys
import os
import yaml
import re
import stat
import fnmatch
import pathlib
from  pathlib import PurePath
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
#        m = P_PREFIX.match(path)
#        if m:
#            self._prefix = m.group('prefix')
#            path = m.group('path')

        m = P_PATH.match(path)
        self._prefix = m.group('prefix')
        self._folder = m.group('folder')
        self._relpath = m.group('relpath')
        self._middle = " ".join(self._relpath.split('/')[:-1])
        self._name = os.path.basename(self._path)
        self._fullname = self._name + self._ext

        self._storage_path = storage
        self._is_create = is_create
        self._id = id
        import pathlib
        print(self._prefix, '===================================$$$')

        self._wd = pathlib.PurePath(os.path.abspath('.')).as_posix()
        self._build_dir = None

        self._initialize()
#        log.debug("storage_path: %s\nfilename:%s\n" % (self._storage_path, self._filename))

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
        print('[*----*]', filename)
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
            rpath = project.reference.replace('@', '/')
            storage = storage or self.storage_path
            folder = join(storage, rpath, self._folder, self.id)
            return join(folder, m, self._name), folder
        folders = ['bin'] if self._folder == 'package' else ['bin', '']
        folders = [self._middle] if self._middle else folders
        for m in folders:
            if where == 'project':
                path, folder = ppath(m)
                print('------------------->', path, folder, '@@@@@@')
                if self._is_program(path):
                    return '${project}/%s' % path, folder
            else:
                path, folder = cpath(m)
                if self._is_program(path):
                    prefix = sempath(self.storage_path, [('project', os.path.abspath('.'))])
                    if prefix is None:
                        return '${storage}/%s' % path, folder
                    else:
                        return '%s/%s' % (prefix, path), folder

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
        wd = os.path.abspath('.')
        sub_folder = 'bin' if self._is_windows else 'lib'
        maps = [('project', wd), ('storage', storage)]

        # build artifacts
        if self._is_create and self._folder in ['build', 'package']:
            rpath = project.reference.replace('@', '/')
            # <reference>/package/<id>/<lib|bin>
            path = join(storage, rpath, self.id, sub_folder)
            dirs.append(path)
        else:
            root = join(outdir, self._folder)
            libpath_dir = join(root, sub_folder)
            for i in [libpath_dir, root]:
                path = sempath(i, [('project', wd), ('storage', storage)])
                if not path:
                    raise ENotFoundError('lib path %s not in outdir %s' % (path, project.out_dir))
                dirs.append(path)


        # dependencies
        # build command will use editable info which saved in conanbuildinfo.txt
        # create command use conaninfo.txt
        if self._is_create or self._folder in ['package']:
            info = conaninfo(self._build_dir)
            for i in info.full_requires.serialize():
                folder = i.replace('@', '/').replace(':', '/package/')
                folder = join(storage, folder, sub_folder)
                path = sempath(folder, maps)
                dirs.append(path)
        else:
            cpp = conanbuildinfo(self._build_dir)
            libdirs = cpp.bindirs if self._is_windows else cpp.libdirs
            for i in libdirs:
                path = sempath(i, maps)
                dirs.append(path)

        return dirs

    @property
    def dynamic_libs(self):
        libs = {}
        for libd in self.libpath:
            d = Template(libd).substitute(outdir=self._project.folder.out, project=self._wd, storage=self.storage_path)
            if not os.path.exists(d):
                continue

            for name in os.listdir(d):
                filename = PurePath('%s/%s' % (libd, name)).as_posix()
                path = PurePath(os.path.join(d, name)).as_posix()
                if os.path.isdir(path):
                    continue

                if self._is_windows and fnmatch.fnmatch(name, "*.dll"):
                    libs[name] = {'target': filename, 'symbol': False, 'origin': filename, 'host': PLATFORM}
                    continue  # only for debug

                if not fnmatch.fnmatch(name, '*.so*') or not self._is_linux:
                    continue

                if os.path.islink(path):
                    p = os.readlink(path)
                    if os.path.isabs(p):
                        target = self._path(p)
                    else:
                        target = PurePath('%s/%s' % (libd, p)).as_posix()
                    assert(target)
                    libs[name] = {'target': target, 'symbol': True, 'origin': filename, 'host': PLATFORM}
                else:
                    if is_elf(path):
                        libs[name] = {'target': filename, 'symbol': False, 'origin': filename, 'host': PLATFORM}
                        continue
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
            s = Template(path).substitute(storage=r'%EPM_SANDBOX_STORAGE%',
                                          project=r'%EPM_SANDBOX_PROJECT%')
            return pathlib.PurePath(s).as_posix()

        filename = _(self._filename)

        libdirs = [_(x) for x in self.libpath]

        template = self._template('windows.j2')
        return template.render(libdirs=libdirs, filename=filename, name=name,
                               folder=self._project.folder,
                               profile=self._project.profile,
                               scheme=self._project.scheme,
                               arguments=" ".join(self._argv))

    def _linux(self, name):
        libdirs = []

        filename = self._filename

        template = self._template('linux.j2')
#        image = 'None'
#        shell = '/bin/bash'
#        try:
#           image=self._docker_image
#           shell=self._docker_shell
#        except:
#            pass
        docker = self._project.profile.docker.runner or {}
        docker = dict({'image': 'alpine', 'shell': '/bin/bash', 'home': '/tmp'}, **docker)

        return template.render(libdirs=libdirs, filename=filename, name=name,
                               dylibs=self.dynamic_libs,
                               docker=docker,
                               image=docker['image'],
                               shell=docker['shell'],
                               home=docker['home'],
                               folder=self._project.folder,
                               profile=self._project.profile,
                               scheme=self._project.scheme,
                               arguments=" ".join(self._argv))

    def _linux_windows_docker(self, name):
        def _(path):
            s = Template(path).substitute(#outdir=r'$EPM_SANDBOX_OUTDIR',
                                          storage=r'$EPM_SANDBOX_STORAGE',
                                          project=r'$EPM_SANDBOX_PROJECT',
                                          folder=self._project.folder,
                                          profile=self._project.profile,
                                          scheme=self._project.scheme
                                          )
            return PurePath(s).as_posix()

        filename = _(self._filename)

        libdirs = [_(x) for x in self.libpath]

        template = self._template('linux.cmd.j2')
        
        docker = self._project.profile.docker.runner or {}
        docker = dict({'image': 'alpine', 'shell': '/bin/bash', 'home': '/tmp'}, **docker)

        return template.render(libdirs=libdirs, filename=filename, name=name,
                               dylibs=self.dynamic_libs,
                               docker=docker,
                               image=docker['image'],
                               shell=docker['shell'],
                               home=docker['home'],
                               folder=self._project.folder,
                               profile=self._project.profile,
                               scheme=self._project.scheme,
                               arguments=" ".join(self._argv))

#        return template.render(libdirs=libdirs, filename=filename, name=name,
#                               image=image,
##                               shell=shell,
 #                              home=home,
 #                              scheme=self._project.scheme.name,
 #                              arguments=" ".join(self._argv))

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

#        with open(filename + '-dynamic-libs.yaml', 'w') as f:

#            yaml.safe_dump(self.dynamic_libs, f, default_flow_style=False, indent=2)










