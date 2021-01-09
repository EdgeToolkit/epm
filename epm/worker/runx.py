import os
from epm import DATA_DIR
from epm.utils import abspath, load_module
from epm.worker import Worker
from epm.tools.extension import Definition
import shutil

class RunX(Worker):


    def __init__(self, name, namespace=None, project=None, api=None):
        super(RunX, self).__init__(api)
        self.name = name
        self.namespace = namespace
        self.project = project
        self.api = api
        self._builtin_prototype = None
        self._builtin_extension = None
        self.workbench = os.environ.get('EPM_WORKBENCH') or None
        if not self.api and self.project:
            self.api = self.project.api

        self.definition = Definition.load(name,project, os.environ.get('EPM_WORKBENCH'))

    @property
    def builtin_prototype(self):
        if self._builtin_prototype is None:
            p_dir = os.path.join(DATA_DIR, 'extension', 'prototype')
            self._builtin_prototype = {}
            for name in os.listdir(p_dir):
                path = os.path.join(p_dir, name)
                if os.path.isdir(path):
                    self._builtin_prototype[name] = path
        return self._builtin_prototype

    @property
    def builtin_extension(self):
        if self._builtin_extension is None:
            p_dir = os.path.join(DATA_DIR, 'extension')
            self._builtin_extension = {}
            for name in os.listdir(p_dir):
                path = os.path.join(p_dir, name)
                if name in ['prototype']:
                    continue
                if os.path.isdir(path):
                    self._builtin_prototype[name] = path
        return self._builtin_extension


    def _load_extension(self):
        try:
            definition = Definition.load(self.name, self.namespace, self.project, self.workbench)
        except FileNotFoundError as e:
            if self.namespace in [None, '', 'epm'] and self.name in self.builtin_extension:
                ext_dir = abs(f'~/.epm/extension/epm')
                if self.workbench:
                    ext_dir =  abspath(f'~/.epm/.workbench/{self.workbench}/extension/epm')
                shutil.copytree(self.builtin_extension[self.name], ext_dir)
                definition = Definition.load(self.name, self.namespace, self.project, self.workbench)
            else:
                raise e
        attribute = definition.attribute









    def exec(self, runner=None, argv=[]):




