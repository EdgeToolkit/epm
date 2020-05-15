import os
import shutil
import yaml
from epm.worker import Worker
from epm.model.project import Project
from conans.tools import environment_append

_CONANFILE ='''
from conans import ConanFile
class Donwload(ConanFile):
    name = download
    requires = '%s'
'''
class Downloader(Worker):

    def __init__(self, api=None):
        super(Downloader, self).__init__(api)

    def exec(self, param):
        path = os.path.abspath(param.get('directory', '.'))
        reference = param.get('reference')
        storage = param.get('cache', None)
        import tempfile
        if storage is None:
            storage = tempfile.mkdtemp()
        storage = os.path.abspath(storage)
        if not os.path.exists(storage):
            os.makedirs(storage)

        conan = self.api.conan

        project = Project(param.get('PROFILE'), param.get('SCHEME'), self.api)
        profile = project.profile
        scheme = project.scheme
        profile_name = os.path.join(storage, 'profile')
        profile.save(profile_name)

        conanfile = os.path.join(storage, 'conanfile.txt')
        with open(conanfile, 'w') as f:
            f.write('[requires]\n{}\n'.format("\n".join(reference)))

        for ref in reference:
            options = ['%s=%s' % (k, v) for (k, v) in scheme.deps_options(ref, scheme.name).as_list()]
        from conans import tools

        with environment_append({'CONAN_STORAGE_PATH': storage}):
            with tools.chdir(storage):
                info = conan.install(conanfile, name='downloader', version='0.1',
                              options=options, profile_names=[profile_name])
                assert not info['error']
                with open(os.path.join(path, 'download.yml'), 'w') as f:
                    yaml.dump(info, f)

        self.copy(info, path)


    def copy(self, info, path):
        copyed = {}
        all = info['installed']
        for package in all:
            recipe = package['recipe']
            for pkg in package['packages']:
                cpp = pkg['cpp_info']
                rootpath = cpp['rootpath']
                Id = pkg['id']
                ref = recipe['id']
                name = cpp['name']
                if name not in copyed:
                    copyed[name] = {
                        'id': Id,
                        'ref': ref
                    }
                else:
                    if copyed[name]['id'] != Id or copyed[name]['ref'] != ref:
                        raise Exception('Conflict package %s:%s <==> %s:%s' % (
                            copyed[name]['id'], copyed[name]['ref'], Id, ref
                        ))
                shutil.copytree(rootpath, os.path.join(path, name))

