import os
import sys
import unittest
import argparse
import epm
import fnmatch
from epm import commands

_DIR = os.path.dirname(__file__)
_DESCRIPTION = 'EPM (%s) unittest utils, which installed on %s' % (epm.__version__, os.path.dirname(epm.__file__))


def Main(args):
    parser = argparse.ArgumentParser(description=_DESCRIPTION,
                                     formatter_class=commands.SmartFormatter)

    parser.add_argument('-p', '--pattern', type=str, default='test_*.py',
                        help='pattern of the the test file to run.')

    parser.add_argument('-d', '--dir', type=str, default=None,
                        help='only specified directory')

    args = parser.parse_args(args)

    cases =unittest.defaultTestLoader.discover(_DIR, pattern=args.pattern, top_level_dir=None)

    runner = unittest.TextTestRunner(descriptions=_DESCRIPTION, verbosity=2)
    return runner.run(cases)


def run():
    Main(sys.argv[1:])


if __name__ == '__main__':
    run()