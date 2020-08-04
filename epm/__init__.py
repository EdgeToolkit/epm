# Allow conans to import ConanFile from here
# to allow refactors
import os
import logging

__version__ = '0.1.0-webkit-100'


HOME_DIR = os.path.join(os.path.expanduser('~'), '.epm')
DATA_DIR = os.path.normpath('%s/data' % os.path.dirname(__file__))


logger = logging.getLogger()
_file_handler = None


def set_logger(filename, level=logging.INFO):
    global _file_handler
    if filename is None:
        if _file_handler:
            _file_handler.close()
        return

    logger.setLevel(level=level)
    handler = logging.FileHandler(filename)

    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(filename)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    _file_handler = handler


