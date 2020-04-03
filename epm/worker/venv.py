#import os
#import glob
#import fnmatch
#from epm.errors import EException
#from epm.worker import Worker
#from epm.model.project import Project
#from epm.errors import APIError
#from epm.model.sandbox import Program
#from epm.util import is_elf, system_info
#
#
#PLATFORM, ARCH = system_info()
#
#
#
#class VEnv(Worker):
#
#    def __init__(self, api=None):
#        super(VEnv, self).__init__(api)
#
#    def exec(self, param):
#        param = param or {}
#        name = param.get('name')
#        command = param['command']
#        if command == 'shell':
#            self._shell(param)
#