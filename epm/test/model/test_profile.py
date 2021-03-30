import os
import unittest

from epm import DATA_DIR as EPM_DATA_DIR
#from epm.model.profile import load_manifest, Profile
#
#
#class TestProfile(unittest.TestCase):
#    PROFILE_DIR = os.path.join(EPM_DATA_DIR, 'profiles')
#    manifest = load_manifest(PROFILE_DIR)
#
#    def test_load_manifest(self):
#        m = self.manifest
#        for i in ['vs2019', 'vs2019-debug', 'vs2019d']:
#            self.assertIn(i, m)
#
#        # vs2019
#        vs2019d = m['vs2019d']
#        self.assertEqual(vs2019d['family'], 'msvc')
#        self.assertEqual(vs2019d['group'], 'vs2019')
#        self.assertEqual(vs2019d['name'], 'vs2019-debug')
#
#    def test_vs2019d_profile(self):
#        profile = Profile('vs2019d', self.PROFILE_DIR)
#        self.assertEqual(profile.settings['compiler'], 'Visual Studio')
#        self.assertEqual(profile.settings['compiler.version'], '16')
#        self.assertEqual(profile.settings['build_type'], 'Debug')
#







