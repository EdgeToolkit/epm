import os
from epm.worker import Worker
from epm.model.project import Project
from conans.tools import environment_append


class Uploader(Worker):

    def __init__(self, api=None):
        super(Uploader, self).__init__(api)

    def exec(self, param):
        print('=========================----===================')
        print(os.environ)
        print('=========================----===================')

        profile = param.get('PROFILE')
        scheme = param.get('SCHEME')
        storage = param.get('storage')
        storage = os.path.abspath(storage) if storage else self.api.conan_storage_path

        project = Project(profile, scheme, self.api)
        package_id = project.buildinfo['package_id']
        reference = project.reference
        remote = param.get('remote') or project.group

        from conans.client.cmd.uploader import UPLOAD_POLICY_FORCE

        with environment_append(dict(os.environ, **{'CONAN_STORAGE_PATH': storage})):
            info = self.conan.upload(pattern=reference, package=package_id,
                                     policy=UPLOAD_POLICY_FORCE,
                                     remote_name=remote, all_packages=False)
