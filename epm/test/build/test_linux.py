import os
from subprocess import run as call
from subprocess import PIPE
from epm.util.files import mkdir, rmdir
from epm.test import TestCase, CONFIG
from unittest import skipIf, skip

Config = CONFIG

is_linux = bool(Config.platform != 'Linux')
docker_startup = Config.is_docker_startup


@skipIf(Config.platform != 'Linux' or not Config.is_docker_startup,
        'GCC5_Docker: %s, docker %s startup.'
        % (Config.platform, '' if Config.is_docker_startup else 'not'))
class GCC5_Docker(TestCase):
    conan_server = True

    def test_lib_gcc5(self):
        mkdir('lib1')
        os.chdir('lib1')
        call(['epm', 'init', 'lib'], check=True)
        call(['epm', 'build', '--scheme', 'gcc5'], check=True)
        call(['epm', 'build', '--scheme', 'gcc5'], check=True)
        proc = call(['epm', 'sandbox', '--scheme', 'gcc5', 'test_package'], stdout=PIPE, stderr=PIPE)
        self.assertEqual(proc.returncode, 0)

    def test_app_gcc5(self):
        mkdir('app1')
        os.chdir('app1')
        call(['epm', 'init', 'app'], check=True)
        call(['epm', 'build', '--scheme', 'gcc5'], check=True)
        proc = call(['epm', 'sandbox', '--scheme', 'gcc5', 'app1'], stdout=PIPE, stderr=PIPE)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual('app1 0.0.1', str(proc.stdout, encoding='utf-8').strip())
