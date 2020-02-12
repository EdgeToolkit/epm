import os

from epm.util.files import mkdir, rmdir
from epm.test import TestCase, CONFIG
from unittest import skipIf
from subprocess import run as call
from subprocess import PIPE

Config = CONFIG


@skipIf(not Config.with_vs2019, 'BuildVS2019: Visual Studio 2019 not installed')
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
        return
        mkdir('app1')
        os.chdir('app1')
        call('epm init app', check=True)
        call('epm build --scheme vs2019')
        import subprocess
        proc = call('epm sandbox --scheme vs2019 app1', stdout=PIPE, stderr=PIPE)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual('app1 0.0.1', str(proc.stdout, encoding='utf-8').strip())


#@skipIf(Config.platform != 'Windows' or not Config.is_docker_startup, 'GCC5BuildInWindowsDocker: ')
#class GCC5BuildInWindowsDocker(TestCase):
#    conan_server = True
#
#    def test_lib_gcc5_in_win_docker(self):
#        mkdir('lib1')
#        os.chdir('lib1')
#        call('epm init lib', check=True)
#        call('epm build --scheme gcc5 --runner docker')
#        proc = call('epm sandbox --scheme vs2019 test_package')
#        self.assertEqual(proc.returncode, 0)