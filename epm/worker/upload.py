import os
from epm.worker import Worker, DockerBase, param_encode
from epm.model.project import Project
from epm.errors import EException, APIError
from epm.tool.conan import ConanMeta


class Uploader(Worker):

    def __init__(self, api=None):
        super(Uploader, self).__init__(api)

    def _exec(self, project, steps):
        for i in self.conan.editable_list():
            self.conan.editable_remove(i)

        for i in ['configure', 'package', 'install', 'test']:
            if i in steps:
                fn = getattr(self, '_%s' % i)
                self.out.highlight('[building - %s ......]' % i)
                fn(project)

    def exec(self, param):
        meta = ConanMeta()
        project = Project(param['scheme'], self.api)
        scheme = project.scheme
        storage = param.get('storage')
        remote = param.get('remote') or meta.user
        reference = meta.reference
        package_id = None

        storage_path = os.path.abspath(storage) if storage else self.api.conan_storage_path
        all_packages = not scheme

        if scheme:
            package_id = project.buildinfo['package_id']

        from conans.client.cmd.uploader import UPLOAD_POLICY_FORCE

        info = self.conan.upload(pattern=reference, package=package_id, policy=UPLOAD_POLICY_FORCE,
                                 remote_name=remote, all_packages=all_packages)
