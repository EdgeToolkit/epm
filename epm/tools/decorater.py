import os
from conans.tools import chdir as _ChDir
from conans.tools import mkdir

def chdir(*args, **kwargs):
    WD, = args
    def _wrapper(func):
        def _decorater(params):

            mkdir(WD)            
            with _ChDir( WD ):
                func(params)
        return _decorater
    return _wrapper

