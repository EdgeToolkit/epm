#!/usr/bin/env python3
import os
import sys
import argparse
import yaml
import subprocess
import fnmatch
from urllib.parse import urlparse

_DIR = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, f"{_DIR}/..")

from epm import __version__
from epm.utils import ObjectView

_NAMEs = ['conan-hisiv300', 'conan-hisiv400', 'conan-himix100',
          'linaro-gcc5-armv7', 'linaro-gcc6-armv7', 'linaro-gcc7-armv7', 'linaro-gcc8-armv7',
          'linaro-gcc5-armv8', 'linaro-gcc6-armv8', 'linaro-gcc7-armv8', 'linaro-gcc8-armv8',

          'gcc5', 'gcc6', 'gcc7', 'gcc8',

          'gcc5-armv7', 'gcc6-armv7', 'gcc7-armv7', 'gcc8-armv7',
          'gcc5-armv8', 'gcc6-armv8', 'gcc7-armv8', 'gcc8-armv8',
          'hisiv300', 'hisiv400',
          'himix100'
          ]

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

import re
def build(name, version, config):
    GCC_ARM = re.compile(r'^gcc(?P<version>\d+)\-(?P<armv>armv\d+)')
    LINARO_GCC = re.compile(r'linaro-gcc(?P<version>\d+)\-(?P<armv>armv\d+)')
    context = {'profile': name, 'version': version, 'config': config}

    if name.startswith('conan-'):
        filename = name.replace('-', '/')
    elif name.startswith('linaro-'):
        filename = 'linaro'
        m = re.match(LINARO_GCC, name)
        print(m, m.groups(), m.group('armv'))
        context.update({'version': m.group('version'),
                        'arch': 'aarch64' if m.group('armv') == 'armv8' else 'arm'})
    elif name.startswith('gcc'):
        filename = 'GCC'
        m = re.match(GCC_ARM, name)
        if m:
            filename = 'GCC-ARM'
            context.update({'version': m.group('version'),
                            'arch': 'aarch64' if m.group('armv') == 'armv8' else 'arm'})

    elif name.startswith('hi'):
        filename = 'HiSi'
    from epm.utils import Jinja2

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
    parser.add_argument('-c', '--config', default=None,
                        help="config file path. YAML format example\n")
    args = parser.parse_args()
#    args.config = os.path.expanduser(args.config)
    targets = match(args.name)
    print("Build ", ",".join(targets))
    if not targets:
        print("No images build. supported targets as below:")
        print("-- {}".format("\n-- ".join(_NAMEs)))
        return 0
    path = args.config
    if not path:
        path = 'config.yml'
        if not os.path.exists(path):
            path = os.path.join(_DIR, 'config.yml')
            if not os.path.exists(path):
                raise Exception('Missing config.yml')
    print("Using config file: {}".format(os.path.abspath(path)))

    with open(path) as f:
        data = yaml.safe_load(f)
        data = dict({'htt_proxy': None, 'pypi': None, 'archive_url': None,
                     'tarball': {}}, **data)
        archive_url = data['archive_url']
        tarball = data['tarball']
        if archive_url:
            for k in tarball:
                tarball[k] = tarball[k].replace("${", "{").format(**data)
        pypi = data['pypi']
        if pypi:
            pip_options = f"--proxy {pypi}"
            url = urlparse(pypi)
            if url.scheme == 'http':
                host = url.netloc.split(':')[0]
                data['pypi_trusted_host'] = host
                pip_options += f" --trusted-host {host}"
            data['pip_options'] = pip_options

    config = ObjectView(data)
    for name in targets:
        if name.startswith('conan-') or name.startswith('linaro-'):
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

