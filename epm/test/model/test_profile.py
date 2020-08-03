import os
import unittest

from epm import DATA_DIR as EPM_DATA_DIR
from epm.model.profile import load_manifest


class TestProfile(unittest.TestCase):
    PROFILE_DIR = os.path.join(EPM_DATA_DIR, 'profiles')
    manifest = load_manifest(PROFILE_DIR)

    def test_load_manifest(self):
        m = self.manifest
        print('------------------', m)
        self.assertNotIn(['vs2019', 'vs2019-debug', 'vs2019d'], list(m.keys()))

        # vs2019
#        vs2019d = m['vs2019d']
#        self.assertEqual(vs2019d['family'], 'msvc')
#        self.assertEqual(vs2019d['group'], 'vs2019')
#        self.assertEqual(vs2019d['name'], 'vs2019-debug')




