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

    parser.add_argument('-f', '--folder', type=str, default='*',
                        help='pattern of the the test file to run.')

    parser.add_argument('-p', '--pattern', type=str, default='test_*.py',
                        help='pattern of the the test file to run.')

    args = parser.parse_args(args)


    suites = []
    for i in os.listdir(_DIR):
        path = os.path.join(_DIR, i)

        if not os.path.isdir(path):
            continue

        if i in ['data', '__pycache__']:
            continue

        if not fnmatch.fnmatch(i, args.folder):
            continue
        print(i, '#', args.pattern, '@', path)

        suite = unittest.defaultTestLoader.discover(path, pattern=args.pattern, top_level_dir=None)
        break


    runner = unittest.TextTestRunner(descriptions=_DESCRIPTION, verbosity=2)
    runner.run(suite)


def run():
    Main(sys.argv[1:])


if __name__ == '__main__':
    run()