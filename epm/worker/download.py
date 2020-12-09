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
        is_deps = param.get('deps')
        reference = param.get('reference')
        storage = param.get('storage')
        exclude = param.get('exclude') or []

        with environment_append({'CONAN_STORAGE_PATH': os.path.abspath(storage)}) if storage else no_op():
            if is_deps:
                self._download_deps(reference, exclude)
            else:
                self._download_refs(reference)

    def _download_deps(self, reference, exclude):
        if isinstance(reference, str):
            reference = [reference]

        conaninfos = []
        for pattern in reference:
            if os.path.isdir(pattern):
                conaninfos += glob.glob(f"{pattern}/conaninfo.txt")
                conaninfos += glob.glob(f"{pattern}/**/conaninfo.txt", recursive=True)
            elif os.path.isfile(pattern):
                conaninfos = [pattern]
            else:
                conaninfos += glob.glob(f"{pattern}/conaninfo.txt")

        conan = self.api.conan
        conan.create_app()
        remotes = conan.app.load_remotes()
        print(remotes, '###########', remotes.items())
        for remote in remotes.values():
            print('#', remote.name)
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
                for remote in remotes.values():
                    try:
                        conan.download(reference=reference, packages=packages_list, remote_name=remote.name)
                        failed = None
                        break
                    except Exception as e:
                        failed = e
                if failed:
                    raise failed

    def _download_refs(self, reference):
        assert False

