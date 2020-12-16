#!/usr/bin/env python3
import os
import sys
import jinja2
import argparse
import yaml
import subprocess
import fnmatch
from urllib.parse import urlparse

_DIR = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
_EPM_DIR = os.path.normpath(os.path.join(_DIR, '..'))
sys.path.insert(0, _EPM_DIR)
from epm import __version__ as VERSION
#VERSION = __import__(f"{_EPM_DIR}/epm/__init__").__version__

_CONFIG_TEMPLATE = """
conan:
  version: 1.31.2

tarball:
  hisiv300: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv300-linux.tar.gz
  hisiv400: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv400-linux.tar.gz
  hisiv500: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv500-linux.tgz
  hisiv600: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv600-linux.tgz

pip:
  proxy: http://<hostname>:8888
  # --index-url
  index-url: http://<hostname>:8040/repository/pypi/simple
  # pip --trusted-host
  trusted-host: <hostname>
"""

_NAMEs = ['conan-hisiv300', 'conan-hisiv400',
'gcc5', 'gcc5-x86', 'gcc5-armv7', 'gcc5-armv8',
'gcc8', 'gcc8-x86', 'gcc8-armv7', 'gcc8-armv8',
]
# 'gcc5-x86', NOT WORK


def match(patterns):
    if isinstance(patterns, str):
        patterns = [patterns]
    result = []
    for name in _NAMEs:
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                result.append(name)
                break
    return result

def dict2obj(d):
    if isinstance(d, dict):
        n = {}
        for item in d:
            name = item.replace('-', '_')
            if isinstance(d[item], dict):
                n[name] = dict2obj(d[item])
            elif isinstance(d[item], (list, tuple)):
                n[name] = [dict2obj(elem) for elem in d[item]]
            else:
                n[name] = d[item]
        return type('obj_from_dict', (object,), n)
    elif isinstance(d, (list, tuple,)):
        l = []
        for item in d:
            l.append(dict2obj(item))
        return l
    else:
        return d

def render(name, version, j2, config):
    pip_options = f"--proxy {config.pip.proxy}" if config.pip.proxy else ""
    if config.pip.index_url:
        pip_options += f" --index-url {config.pip.index_url}"
    if config.pip.trusted_host:
        pip_options += f" --trusted-host {config.pip.trusted_host}"

    image = name
    if image.endswith('-arm'):
        image +="v7"
    elif image.endswith('-aarch64'):
        image =image.replace("-aarch64", "-armv8")

    kworkds = {'profile': name, 'version': version, 'config': config,'pip_options': pip_options}
    loader = jinja2.FileSystemLoader(searchpath=[os.path.join(_DIR, "templates")])
    env = jinja2.Environment(loader=loader)
    template = env.get_template(j2)
    return template.render(kworkds)


def build(name, version, config):
    if name.startswith('conan-'):
        filename = name.replace('-', '/')
    elif name.startswith('gcc'):
        filename = 'GCC'
    elif name.startswith('hi'):
        filename = 'HiSi'
    
    txt = render(name, version, f"{filename}.j2", config)
    
    
    with open(f".epm/{name}.Dockerfile", 'w') as f:
        f.write(txt)
    command = ['docker', 'build', '-f', f"{name}.Dockerfile", '-t', f'edgetoolkit/{name}:{version}', '.']
    print(command)
    subprocess.run(command, check=True, cwd='.epm')

#
# build x --clear
#
def Main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs='+', help="name of the docker image to build.")
    parser.add_argument('--version', type=str, help="version of the image to build instead read from epm module.")
    parser.add_argument('--build', default=False, action="store_true", help="execute image build")
    parser.add_argument('--clear', default=False, action="store_true", help="clear exist image, if build")
    parser.add_argument('-c', '--config', default="~/config/docker-tools/config.yml", help="config file path. YAML format example\n")
    args = parser.parse_args()
#    name = args.name[0]
    args.config = os.path.expanduser(args.config)
    targets = match(args.name)
    print("Build ", ",".join(targets))
    if not targets:
        print("No images build.")
        return 0

    with open(args.config) as f:
        data = yaml.safe_load(f)
        data = dict({'pip':{'proxy': None, 'index-url': None, 'trusted-host': None}}, **data)
    if not os.path.exists(".epm"):
        os.makedirs(".epm")
    CWD = os.path.abspath('.')
    print(CWD, '-----', _EPM_DIR)
    subprocess.run(['git', 'archive', '--format', 'tar.gz', '--output',
                    f'{CWD}/.epm/epm.tar.gz', 'HEAD '], cwd=_EPM_DIR)    
    config = dict2obj(data)
    for name in targets:
        if name.startswith('conan-'):
            version = config.conan.version
        else:
            version = args.version or VERSION

        if args.clear:
            subprocess.run(['docker', 'rmi', f'edgetoolkit/{name}:{version}'], check=False)
        if args.build:
            build(name, version, config)





if __name__ == '__main__':
    Main()
