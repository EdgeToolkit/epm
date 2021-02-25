# Allow conans to import ConanFile from here
# to allow refactors
import os

__version__ = '0.0.61.8'

HOME_DIR = os.path.join(os.path.expanduser('~'), '.epm')
DATA_DIR = os.path.normpath('%s/data' % os.path.dirname(__file__))
EXTENSIONS_DIR = os.path.normpath('%s/extensions' % os.path.dirname(__file__))
