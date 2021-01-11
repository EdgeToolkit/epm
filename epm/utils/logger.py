import os
import yaml
import shutil
import logging 
import logging.config


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


syslog = get_logger()


class SysLog(object):

    @property
    def logger(self):
        return None

    def open(self, filename='.epm/sys.log', prolog=''):
        pass

    def close(self):
        pass

    def flush(self):
        pass

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

