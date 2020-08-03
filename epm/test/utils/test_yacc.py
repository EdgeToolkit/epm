import os
import unittest
from unittest import mock
from epm.util.mirror import Mirror

from epm.test.utils import DATA_DIR

from epm.util import mirror

_SERVER = 'http://127.0.0.1/archive'

mirror = Mirror(os.path.join(DATA_DIR, 'mirror', 'mirrors.yml'))
class TestMirror(unittest.TestCase):

    def test_basic(self):
        return

        locations = [("https://zlib.net/zlib-1.2.11.tar.gz", '{}/zlib/zlib-1.2.11.tar.gz'.format(_SERVER)),
                     ("https://downloads.sourceforge.net/project/libpng/zlib/1.2.11/zlib-1.2.11.tar.gz",
                      '{}/zlib/zlib-1.2.11.tar.gz'.format(_SERVER)),
                    ]

        for url, path in locations:
            self.assertEqual(path, mirror.find_package('zlib', url))

    def test_ref(self):

        locations = [('libiconv',
                      'https://ftp.gnu.org/gnu/libiconv/libiconv-1.16.tar.gz',
                      '{}/gnu/libiconv/libiconv-1.16.tar.gz'.format(_SERVER)
                      ),

                     ('m4',
                      "https://ftp.gnu.org/gnu/m4/m4-1.4.18.tar.bz2",
                      '{}/gnu/m4/m4-1.4.18.tar.bz2'.format(_SERVER)
                      ),

                     ('gperf',
                      "https://ftp.gnu.org/pub/gnu/gperf/gperf-3.1.tar.gz",
                      '{}/gnu/gperf/gperf-3.1.tar.gz'.format(_SERVER)
                      ),
                    ]

        for name, url, path in locations:
            self.assertEqual(mirror.find_package(name, url), path)

