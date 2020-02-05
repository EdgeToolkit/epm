import os
import unittest




class Utils(unittest.TestCase):

    def test_sempath(self):
        return
        from epm.util import sempath

        # relative
        path = r'1/2/3/4'

        prefixs = [('one', '1'), ('two', '1/2')]
        self.assertEqual('${one}/2/3/4', sempath(path, prefixs))

        prefixs = [('one', '1'), ('two', '1\\2')]
        self.assertEqual('${one}/2/3/4', sempath(path, prefixs))

        prefixs = [('two', '1/2'), ('one', '1')]
        self.assertEqual('${two}/3/4', sempath(path, prefixs))

    def test_get_epm_user_home(self):
        from epm.paths import get_epm_user_home

