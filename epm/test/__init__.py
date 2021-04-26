import os
TOP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TOP_DIR, 'data')


def workdir(*args, **kwargs):
    WD, = args
    def _wrapper(func):
        def _decorater(params):
            from conans.tools import chdir, mkdir
            mkdir(WD)            
            with chdir( WD ):
                func(params)
        return _decorater
    return _wrapper

import yaml
def save_yaml(filename, data):
    path = os.path.abspath(filename)
    directory = os.path.dirname(path)
    mkdir(directory)
    
    with open(filename, 'w') as f:        
        yaml.dump(data, filename, default_flow_style=False)
    
        