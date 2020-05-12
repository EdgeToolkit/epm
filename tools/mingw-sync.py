import os
import time
import re
from download import download
import re
_REPO_LIST_URL='https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win32/Personal%20Builds'\
               '/mingw-builds/installer/repository.txt/download'


_REPO_LIST_URL = r'http://sourceforge.mirrorservice.org/m/mi/mingw-w64'\
                 '/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds/installer/repository.txt'


_VERSIONs = [
    "4.9.4", "4.9.3",
    "5.4.0", "5.2.0"
    "6.3.0",
    "7.1.0",
    "8.1.0"
]









def sync():
    #folder = os.path.join(repo, arch)
    repo_list = 'mingw-builds/repository-origin.txt'
    print(not os.path.exists(repo_list))
    if not os.path.exists(repo_list):
        download(_REPO_LIST_URL, repo_list, progressbar=True, replace=False)

    from collections import namedtuple
    Build = namedtuple('Build', 'version arch threads exception rev url')
    builds = []
    best = {}
    repository = []
    candidates = {}
    with open(repo_list) as f:
        for line in f.readlines():
            data = line.split('|')
            version = data[0].strip()
            arch = data[1].strip()
            threads = data[2].strip()
            exception = data[3].strip()
            rev = data[4].strip()
            url = data[5].strip()
            filename = None

            if version in _VERSIONs:
                filename = line.split('mingw-builds/')[1]
                key = version + arch + threads + exception
                cur = {'rev': rev, 'url': url, 'filename': filename,
                       'desc': line.split("|http")[0] + '|http://172.16.0.119/mirror/mingw-builds/%s' % filename
                       }
                if key not in candidates:
                    candidates[key] = cur
                if rev > cur['rev']:
                    candidates[key] = cur
    for key, it in candidates.items():
        filename = os.path.join('mingw-builds', it['filename'])
        download(url, filename, progressbar=True, replace=False)
        print(it['desc'])

#                download(url, filename, progressbar=True, replace=False)

#                line = line.split("|http")[0] + '|http://172.16.0.119/mirror/mingw-builds/%s' % filename
#                repository.append(line)

#            build = Build(version, arch, threads, exception, rev, url)
#            builds.append(build)
#            key = version + arch + threads + exception

#            if key not in best:
#                best[key] = build

#            if rev > best[key].rev:
#                best[key] = build
    for i in best.values():
        filename = os.path.join(version, 'threads-%s' % threads, exception, os.path.basename(i.url))
        url = 'http://sourceforge.mirrorservice.org/m/mi/mingw-w64/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds'
        url = os.path.join(url, version, 'threads-%s' % threads, exception, os.path.basename(i.url))

        download(url, filename, progressbar=True, replace=False)


#    for name in archives(index):
#        filename = os.path.join(folder, name)
#        if os.path.exists(filename):
#            #print('[exists]', filename)
#            continue
#        url = '%s/%s/%s/%s' % (_Package, repo, arch, name)
#
#        if repo == 'msys':
#            m = _P_MSYS2_PKG.match(name)
#            assert m
#            if m.group('name') in _EXCLUDES:
#                print('skip ', name)
#                continue
#        elif repo == 'mingw':
#            m = _P_MINGW_PKG.match(name)
#            assert m
#            if m.group('name') in _EXCLUDES:
#                print('skip ', name)
#                continue
#        else:
#            pass
#
#        download(url, filename, progressbar=True, replace=False)


sync()

print('Done !!!!')
