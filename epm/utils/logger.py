import os
import yaml
import shutil
import logging 
import logging.config
#from conans.tools import mkdir
#
#
#class SysLogger(object):
#    FILENAME = ".epm/logs/epm.log"
#    NATIVE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
#    DOCKER_FORMAT = '%(asctime)s = %(levelname)s = %(message)s'
#
#    def __init__(self):
#        self._logger = None
#        self._file = None
#        self._console = None
#        self._formatter = None
#
#    def __getattr__(self, item):
#        if item.startswith('_'):
#            return getattr(self, item)
#        else:
#            if self._logger is None:
#                self._open()
#            fn = getattr(self._logger, item)
#            print(fn, '@')
#            return fn
#
#    def _open(self):
#        EPM_DOCKER_IMAGE = os.environ.get('EPM_DOCKER_IMAGE')
#        EPM_DOCKER_CONTAINER_NAME = os.environ.get('EPM_DOCKER_CONTAINER_NAME')
#        docker = bool(EPM_DOCKER_CONTAINER_NAME or EPM_DOCKER_IMAGE)
#        if docker:
#            prolog = f"Setup logger for {EPM_DOCKER_CONTAINER_NAME} image:{EPM_DOCKER_IMAGE}\n"
#        else:
#            prolog = f"Setup logger for shell instance\n"
#
#        mkdir(os.path.dirname(SysLogger.FILENAME))
#
#        self._logger = logging.getLogger("root")
#        print('##', os.path.abspath(SysLogger.FILENAME))
#        self._file = logging.FileHandler(SysLogger.FILENAME)
#        #self._file.setLevel(logging.INFO)
#        formatter = logging.Formatter(SysLogger.NATIVE_FORMAT if docker else SysLogger.DOCKER_FORMAT)
#        self._file.setFormatter(formatter)
#        self._logger.addHandler(self._file)
#
#        self._logger.info(prolog)
#
#    def _close(self):
#
#        if self._logger:
#            self._logger = None
#
#        if self._file:
#            self._file.close()
#            self._file = None
#
#
def get_logger(name=None):
    from epm import DATA_DIR
    from conans.tools import mkdir
    from epm.utils import get_workbench_dir

    path = os.path.join(get_workbench_dir(os.getenv('EPM_WORKBENCH')), 'log-conf.yml')
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


syslog = get_logger()
