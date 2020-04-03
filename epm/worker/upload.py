import os
from epm.worker import Worker, DockerBase, param_encode
from epm.model.project import Project
from epm.errors import EException, APIError
from conans.tools import environment_append

class Uploader(Worker):

    def __init__(self, api=None):
        super(Uploader, self).__init__(api)

    def exec(self, param):
        from epm.tool.conan import PackageMetaInfo
        meta = PackageMetaInfo()
        profile = param.get('PROFILE')
        storage = param.get('storage')
        remote = param.get('remote') or meta.group
        reference = meta.reference
        package_id = None

        storage = os.path.abspath(storage) if storage else self.api.conan_storage_path
        all_packages = not profile

        if profile:
            scheme = param.get('SCHEME')
            project = Project(profile, scheme, self.api)
            package_id = project.buildinfo['package_id']

        from conans.client.cmd.uploader import UPLOAD_POLICY_FORCE


        with environment_append(dict(self.api.config.env_vars,
                                     **{'CONAN_STORAGE_PATH': storage})):
            info = self.conan.upload(pattern=reference, package=package_id,
                                     policy=UPLOAD_POLICY_FORCE,
                                     remote_name=remote, all_packages=all_packages)
