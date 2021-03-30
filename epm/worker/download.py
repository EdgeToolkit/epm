import os
import glob
import shutil
import yaml
import tempfile
from epm.worker import Worker

from conans.tools import environment_append, no_op
from conans.model.info import ConanInfo, PackageReference
from conans.util.files import load, mkdir, rmdir


class Downloader(Worker):

    def __init__(self, api=None):
        super(Downloader, self).__init__(api)

    def exec(self, param):
        reference = param.get('reference')
        storage = param.get('STORAGE')
        exclude = param.get('exclude') or []
        remote = param.get('remote') or []

        with environment_append({'CONAN_STORAGE_PATH': os.path.abspath(storage)}) if storage else no_op():
            if os.path.exists(reference):
                self._download_according_conaninfo(remote, reference, exclude)
            else:
                self._download_refs(remote, reference)

    def _download_according_conaninfo(self, remote, reference, exclude):
        pattern = reference
        if os.path.isdir(pattern):
            conaninfos = glob.glob(f"{pattern}/conaninfo.txt")
            conaninfos += glob.glob(f"{pattern}/**/conaninfo.txt", recursive=True)
        elif os.path.isfile(pattern):
            conaninfos = [pattern]

        conan = self.api.conan
        conan.create_app()
        remotes = remote or [x.name for x in conan.app.load_remotes().values()]

        for filename in conaninfos:
            conaninfo = ConanInfo.loads(load(filename))
            for pref in conaninfo.full_requires:
                reference = repr(pref.ref)
                if pref.ref.name in exclude:
                    continue
                if pref.ref.user is None:
                    if pref.ref.revision:
                        reference = "%s/%s@#%s" % (pref.ref.name, pref.ref.version, pref.ref.revision)
                    else:
                        reference += "@"
                pkgref = "{}#{}".format(pref.id, pref.revision) if pref.revision else pref.id
                packages_list = [pkgref]
                failed = True
                for name in remotes:
                    try:
                        conan.download(reference=reference, packages=packages_list, remote_name=name)
                        failed = None
                        break
                    except Exception as e:
                        failed = e
                if failed:
                    raise failed

    def _download_refs(self, remote, reference):
        assert False

