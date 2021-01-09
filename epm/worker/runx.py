import os
from epm import EXTENSIONS_DIR as EX_DIR
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
        self._builtin = None
        self._definition = None
        self.workbench = os.environ.get('EPM_WORKBENCH') or None


    @property
    def builtin(self):
        if self._builtin is None:
            self._builtin = {}
            for name in os.listdir(EX_DIR):
                path = os.path.join(EX_DIR, name)
                if os.path.exists(f'{path}/extension.yml'):
                    self._builtin[name] = path
        return self._builtin

    @property
    def definition(self):
        if self._definition is None:
            try:
                definition = Definition.load(self.name, self.namespace, self.project, self.workbench)
            except FileNotFoundError as e:
                if self.namespace in [None, '', 'epm'] and self.name in self.builtin:
                    ex_dir = abspath(f'~/.epm/extension/epm')
                    if self.workbench:
                        ex_dir =  abspath(f'~/.epm/.workbench/{self.workbench}/extension/epm')
                    shutil.copytree(self.builtin[self.name], ex_dir)
                    definition = Definition.load(self.name, self.namespace, self.project, self.workbench)
                else:
                    raise e
            self._definition = definition
        return self._definition

    def main(self):
        if self.definition.kind == 'prototype':
            raise Exception('prototype of extension is not runnable.')

        if self.definition.prototype:
            # load prototype












    def exec(self, runner=None, argv=[]):




