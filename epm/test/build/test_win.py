import os

from epm.util.files import mkdir, rmdir
from epm.test import TestCase, CONFIG
from unittest import skipIf, skip
from subprocess import run as call
from subprocess import PIPE

Config = CONFIG


@skipIf(not Config.with_vs2019,
        'VS2019: %s, Visual Studio 2019 not installed' %
        (Config.platform))
class VS2019(TestCase):
    conan_server = True

    def test_lib_vs2019(self):
        mkdir('lib1')
        os.chdir('lib1')
        call('epm init lib', check=True)
        call('epm build --scheme vs2019')
        proc = call('epm sandbox --scheme vs2019 test_package')
        self.assertEqual(proc.returncode, 0)

    def test_app_vs2019(self):
        mkdir('app1')
        os.chdir('app1')
        call('epm init app', check=True)
        call('epm build --scheme vs2019')
        proc = call('epm sandbox --scheme vs2019 app1', stdout=PIPE, stderr=PIPE)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual('app1 0.0.1', str(proc.stdout, encoding='utf-8').strip())


@skipIf(Config.platform != 'Windows' or not Config.is_docker_startup,
        'GCC5BuildInWindowsDocker: %s, docker %s startup.'
        % (Config.platform, '' if Config.is_docker_startup else 'not'))
class GCC5BuildInWindowsDocker(TestCase):
    conan_server = True

    def test_lib_gcc5_in_win_docker(self):
        mkdir('lib1')
        os.chdir('lib1')
        call('epm init lib', check=True)
        call('epm build --scheme gcc5 --runner docker')
        proc = call('epm sandbox --scheme gcc5 test_package', stdout=PIPE, stderr=PIPE)
        self.assertEqual(proc.returncode, 0)

    def test_app_gcc5_in_win_docker(self):
        
        mkdir('app_gcc5_d')
        os.chdir('app_gcc5_d')
        call('epm init app', check=True)
        call('epm build --scheme gcc5.d --runner docker')
        proc = call('epm sandbox --scheme gcc5.d app_gcc5_d', stdout=PIPE, stderr=PIPE)

        self.assertEqual(proc.returncode, 0)
        content = str(proc.stdout, encoding='utf-8').strip()
        lines = content.split('\n')
        text = lines[-1].strip()
        self.assertEqual('app_gcc5_d 0.0.1', text)
