import os
import time
import re
from download import download
import re
_P_MSYS2_PKG = r'(?P<name>(\w[\w\-]*))\-(?P<version>\d+(\.\d+)*\w*(\-\d+)?)(\-any)?\.pkg\.tar\.xz(\.sig)?'
_P_MINGW_PKG = r'mingw\-w64\-(?P<arch>(i686|x86_64))\-(?P<name>(\w[\w\-]*))\-(?P<version>\d+(\.\d+)*\w*(\-\d+)?)(\-any)?\.pkg\.tar\.xz(\.sig)?'
_P_MSYS2_PKG = re.compile(_P_MSYS2_PKG)
_P_MINGW_PKG = re.compile(_P_MINGW_PKG)

_ORIGIN = r'http://repo.msys2.org'
_BASE = r'https://mirrors.tuna.tsinghua.edu.cn/msys2'
_REPO = ['msys', 'mingw', 'distrib']
_ARCH = ['x86_64', 'i686']


_EXCLUDES = [
    'qt5', 'qt5-debug', 'qt5-static', 'qtbinpatcher', 'qtwebkit', 'qtwebkit-tp5',
    'quantlib'
]


def mkdir(path):
    """Recursive mkdir, doesnt fail if already existing"""
    if os.path.exists(path):
        return
    os.makedirs(path)

#'<a href="apr-1.5.1-1-i686.pkg.tar.xz">apr-1.5.1-1-i686.pkg.tar.xz</a>                        04-Nov-2014 17:17               66724'
_origin = r'\<a href="(?P<package>\w\S+\.tar.xz(\.sig)?)"\>'
_origin += r'(?P<name>\w\S+\.tar.xz(\.sig)?)\</a\>'
_origin += r'\s*(?P<date>\S+)\s+'
_origin += r'(?P<time>\S+)\s+'
_origin += r'(?P<size>\d+)'
_origin_P = re.compile(_origin)


_tsinghua = r'\<tr\>\<td class="link"\>\<a href="(?P<package>\S+(\.pkg)?\.tar\.xz(\.sig)?)" title="'
_tsinghua_P = re.compile(_tsinghua)

_Mirrors = {
    'msys2': {'url': r'http://repo.msys2.org', 'pattern': _origin_P },
    'tsinghua': {'url': r'https://mirrors.tuna.tsinghua.edu.cn/msys2', 'pattern': _tsinghua_P}

}


_Index = _Mirrors['tsinghua']['url']
_Package = _Mirrors['tsinghua']['url']
_Pattern = _Mirrors['tsinghua']['pattern']
def archives(filename):
    result = []
    with open(filename) as f:
        for line in f.readlines():
            m = _Pattern.match(line)
            if not m:
                continue
            result.append(m.group('package'))
    return result


def sync(repo, arch):
    folder = os.path.join(repo, arch)
    index_url = '%s/%s/%s' % (_Index, repo, arch)
    index = os.path.join(folder, '_index.html')
    download(index_url, index, progressbar=True, replace=False)
    for name in archives(index):
        filename = os.path.join(folder, name)
        if os.path.exists(filename):
            #print('[exists]', filename)
            continue
        url = '%s/%s/%s/%s' % (_Package, repo, arch, name)

        #if repo == 'msys':
        #    m = _P_MSYS2_PKG.match(name)
        #    assert m
        #    if m.group('name') in _EXCLUDES:
        #        print('skip ', name)
        #        continue
        if repo == 'mingw':
            m = _P_MINGW_PKG.match(name)
            if not m or m.group('name') in _EXCLUDES:
                print('skip ', name)
                continue
        else:
            pass

        download(url, filename, progressbar=True, replace=False)

def main():
    for repo in _REPO:
        for arch in _ARCH:
            sync(repo, arch)


if __name__ == '__main__':
    main()
    print('Done !!!!')
