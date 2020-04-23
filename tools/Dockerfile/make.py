import os
import jinja2
import argparse
from urllib.parse import urlparse

_DIR = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))


def render(args):
    name = args.name[0]
    if not os.path.exists(os.path.join(_DIR, name + '.j2')):
        raise Exception('Jinja2 template %s not exists' % name)

    ccache_dir = '/tmp/epm_cache'
    kworkds = {'name': name,
               'version': args.version,
               'conan_version': args.conan_version,
               'ccache_dir': ccache_dir
               }

    pip_options = ''
    if args.pypi:
        pip_options += ' -i %s' % args.pypi # --index-url
        url = urlparse(args.pypi)
        if url.scheme == 'http':
            pip_options += ' --trusted-host %s' % url.hostname
    if args.http_proxy:
        pip_options += ' --proxy %s' % args.http_proxy

    kworkds['pip_options'] = pip_options
    kworkds['install_epm'] = 'sudo pip install %s %s' % (pip_options, ccache_dir)
    if args.archive_url:
        kworkds['archive_url'] = args.archive_url

    loader = jinja2.FileSystemLoader(searchpath=_DIR)
    env = jinja2.Environment(loader=loader)
    template = env.get_template('%s.j2' % name)
    print('-------------------------------')
    print(kworkds)
    print('-------------------------------')

    return template.render(kworkds)


def Main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', nargs=1, help="name of the docker image to build.")
    parser.add_argument('--version', type=str, help="specify version of the image to build instead read from epm module.")
    parser.add_argument('--conan_version', type=str, help="version of the conan.")
    parser.add_argument('--pypi', default=None, help="Python package index server.")
    parser.add_argument('--http_proxy', default=None, help="http proxy url")
    parser.add_argument('--archive_url', default=None, help="base url where store Hisilicon toolchain tarballs.)")
    parser.add_argument('--build', default=False, action="store_true", help="execute image build")
    parser.add_argument('--clear', default=False, action="store_true", help="clear exist image, if build")
    args = parser.parse_args()
    name = args.name[0]
    print(args)
    for i in ['epm', 'README.md', 'pylint.cnf', 'setup.cfg', 'setup.py']:
        if not os.path.exists(i):
            raise Exception('You may not run this script in epm root directory.')
    print('-- Generate dockerfile for %s:%s %s' % (name, args.version, ' and build' if args.build else ''))

    filename = 'Dockerfile-%s' % name
    txt = render(args)
    with open(filename, 'w') as f:
        f.write(txt)

    if args.build:
        import subprocess
        if args.clear:
            command = ['docker', 'rmi', 'epmkit/%s:%s' % (name, args.version)]
            subprocess.run(command, check=False)

        command = ['docker', 'build', '.', '-f', filename, '-t', 'epmkit/%s:%s' % (name, args.version)]
        subprocess.run(command, check=True)


if __name__ == '__main__':
    Main()
