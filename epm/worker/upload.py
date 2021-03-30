import os
from epm.worker import Worker
from conans.tools import environment_append
from epm.errors import EConanException
from epm.utils import PLATFORM, abspath
from conans.client.cmd.uploader import UPLOAD_POLICY_FORCE


class Uploader(Worker):

    def __init__(self, api=None):
        super(Uploader, self).__init__(api)

    def exec(self, param):
        profile = param.get('PROFILE')
        scheme = param.get('SCHEME')
        storage = param.get('STORAGE')
        remote = param.get('remote', None)
        env_vars = {} #{'CONAN_REVISIONS_ENABLED': '1'}
        if storage:
            env_vars = {'CONAN_STORAGE_PATH': abspath(storage)}

        with environment_append(env_vars):
            project = self.api.project(profile, scheme)
            package_id = project.record.get('package_id')
            reference = str(project.reference)
            info = self.conan.upload(pattern=reference, package=package_id,
                                     policy=UPLOAD_POLICY_FORCE,
                                     remote_name=remote, all_packages=False)
            if info['error']:
                raise EConanException('configure step failed on conan.install.', info)
