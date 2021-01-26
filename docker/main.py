#!/usr/bin/env python3
import os
import sys
import argparse
import yaml
import subprocess
import fnmatch

_DIR = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, f"{_DIR}/..")

from epm import __version__
from epm.utils import ObjectView


_CONFIG_TEMPLATE = """
conan:
  version: 1.31.2

tarball:
  hisiv300: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv300-linux.tar.gz
  hisiv400: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv400-linux.tar.gz
  hisiv500: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv500-linux.tgz
  hisiv600: http://<hostname>/archive/HiSilicon/GCC/arm-hisiv600-linux.tgz
  himix100: http://<hostname>/archive/HiSilicon/GCC/arm-himix100-linux.tgz

pip:
  proxy: http://<hostname>:8888
  # --index-url
  index-url: http://<hostname>:8040/repository/pypi/simple
  # pip --trusted-host
  trusted-host: <hostname>
"""

_NAMEs = ['conan-hisiv300', 'conan-hisiv400', 'conan-himix100',
          'gcc5', 'gcc5-x86', 'gcc5-armv7', 'gcc5-armv8',
          'gcc8', 'gcc8-x86', 'gcc8-armv7', 'gcc8-armv8',
          'hisiv300', 'hisiv400',
          'himix100'
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


def build(name, version, config):
    if name.startswith('conan-'):
        filename = name.replace('-', '/')
    elif name.startswith('gcc'):
        filename = 'GCC'
    elif name.startswith('hi'):
        filename = 'HiSi'
    from epm.utils import Jinja2

    pip_options = f"--proxy {config.pip.proxy}" if config.pip.proxy else ""
    if config.pip.index_url:
        pip_options += f" --index-url {config.pip.index_url}"
    if config.pip.trusted_host:
        pip_options += f" --trusted-host {config.pip.trusted_host}"

    context = {'profile': name, 'version': version, 'config': config, 'pip_options': pip_options}

    j2 = Jinja2(f"{_DIR}/templates")

    outfile = f".epm/{name}.Dockerfile"
    j2.render(f"{filename}.j2", context=context, outfile=outfile)
    
    command = ['docker', 'build', '-f', f"{name}.Dockerfile", '-t', f'edgetoolkit/{name}:{version}', '.']
    print(" ".join(command))
    subprocess.run(command, check=True, cwd='.epm')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs='+', help="name of the docker image to build.")
    parser.add_argument('--version', type=str, help="version of the image to build instead read from epm module.")
    parser.add_argument('--build', default=False, action="store_true", help="execute image build")
    parser.add_argument('--clear', default=False, action="store_true", help="clear exist image, if build")    
    parser.add_argument('-c', '--config', default="~/config/docker-tools/config.yml",
                        help="config file path. YAML format example\n")
    args = parser.parse_args()
    args.config = os.path.expanduser(args.config)
    targets = match(args.name)
    print("Build ", ",".join(targets))
    if not targets:
        print("No images build. supported targets as below:")
        print("-- {}".format("\n-- ".join(_NAMEs)))
        return 0

    with open(args.config) as f:
        data = yaml.safe_load(f)
        data = dict({'pip': {'proxy': None, 'index-url': None, 'trusted-host': None}}, **data)

    config = ObjectView(data)
    for name in targets:
        if name.startswith('conan-'):
            version = config.conan.version
        else:
            version = args.version or __version__

        if args.clear:
            command = ['docker', 'rmi', f'edgetoolkit/{name}:{version}']
            subprocess.run(command, check=False)
        if args.build:
            build(name, version, config)


if __name__ == '__main__':
    sys.exit(main())

