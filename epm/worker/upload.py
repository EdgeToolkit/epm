import os
from epm.worker import Worker
from conans.tools import environment_append
from epm.errors import EConanException
from epm.utils import PLATFORM
from conans.client.cmd.uploader import UPLOAD_POLICY_FORCE


class Uploader(Worker):

    def __init__(self, api=None):
        super(Uploader, self).__init__(api)

    def exec(self, param):

        profile = param.get('PROFILE')
        scheme = param.get('SCHEME')
        storage = param.get('storage')

        project = self.api.project(profile, scheme)
        package_id = project.record.get('package_id')
        reference = str(project.reference)

        remote = param.get('remote', None)

        storage_path = f"{storage}" if storage else self.api.conan_storage_path
        storage_path = os.path.normpath(os.path.abspath(storage_path))

#        short_path = f"{storage}/short" if storage else self.api.conan_storage_path
#        short_path = os.path.normpath(os.path.abspath(short_path))

        env_vars = {'CONAN_STORAGE_PATH': storage_path}
#        if PLATFORM == 'Windows' and os.path.isdir(short_path):
#            env_vars['CONAN_USER_HOME_SHORT'] = short_path

        with environment_append(env_vars):
            info = self.conan.upload(pattern=reference, package=package_id,
                                     policy=UPLOAD_POLICY_FORCE,
                                     remote_name=remote, all_packages=False)
            if info['error']:
                raise EConanException('configure step failed on conan.install.', info)
