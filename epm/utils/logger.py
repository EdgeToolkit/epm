import os
import yaml
import shutil
import logging 
import logging.config
from epm.utils import abspath
from conans.tools import mkdir
import stat

def get_logger(name=None):
    from epm import DATA_DIR
    from conans.tools import mkdir
    from epm.utils import get_workbench_dir
    workbench_dir = get_workbench_dir(os.getenv('EPM_WORKBENCH', None))
    path = os.path.join(workbench_dir, 'log-conf.yml')
    if not os.path.exists(path):
        mkdir(os.path.dirname(path))
        shutil.copy(os.path.join(DATA_DIR, 'log-conf.yml'), path)

    with open(path) as f:
        conf = yaml.safe_load(f)

    mkdir('.epm/logs')
    logging.config.dictConfig(conf)
    name = name or "epm"
    name = f"docker_{name}" if os.environ.get('EPM_DOCKER_IMAGE') else f"{name}"

    return logging.getLogger(name)


#syslog = get_logger()


class SysLog(object):
    FILENAME = '.epm/log.txt'
    FORMATTER = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    def __init__(self):
        self._logger = None
        self._handler = None
        self._name = None
        self.filename = abspath(self.FILENAME)

    @property
    def logger(self):
        if self._logger is None:
            level = os.getenv('EPM_LOG_LEVEL') or ""
            level = logging._nameToLevel.get(level.upper()) or logging.INFO
            
            logger = logging.getLogger(self._name)
            logger.setLevel(level=level)
            self._logger = logger
            self._attach_handle(self._logger)
        return self._logger
        #return logging.getLogger(self._name) if self._name else self._logger

    def _attach_handle(self, logger):
        if self._handler is None:
            mkdir(os.path.dirname(self.filename))
            formatter = logging.Formatter(self.FORMATTER)
            self._handler = logging.FileHandler(self.filename, mode='a')
            self._handler.setFormatter(formatter)
            logger.addHandler(self._handler)

    def open(self, name=None, prolog=''):

        self._name = name or self._name

        directory = os.path.dirname(self.filename)
        STAT = stat.S_IWOTH | stat.S_IROTH | \
               stat.S_IWGRP | stat.S_IRGRP | \
               stat.S_IWUSR | stat.S_IRUSR
        mkdir(directory)
        mode = 'a' if os.path.exists(self.filename) else 'w'
        with open(self.filename, mode=mode) as f:
            f.write(prolog)
        if mode == 'w':
            os.chmod(self.filename, STAT)

    def close(self):
        if self._handler:
            if self._logger:
                self._logger.removeHandler(self._handler)
            self._handler.flush()
            self._handler.close()
            self._handler = None

    def flush(self):
        if self._handler:
            self._handler.flush()

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

syslog = SysLog()
