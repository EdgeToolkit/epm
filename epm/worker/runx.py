import os
from epm import EXTENSIONS_DIR as EX_DIR
from epm.utils import abspath, load_module
from epm.worker import Worker
from epm.tools.extension import Definition
import shutil


class RunX(Worker):

    def __init__(self, name, project=None, api=None):
        super(RunX, self).__init__(api)
        token = name.split(':')
        namespace = None
        if token == 1:
            name = token[0]
        else:
            namespace = token[0]
            name = token[1]

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
                        ex_dir = abspath(f'~/.epm/.workbench/{self.workbench}/extension/epm')
                    shutil.copytree(self.builtin[self.name], ex_dir)
                    definition = Definition.load(self.name, self.namespace, self.project, self.workbench)
                else:
                    raise e
            self._definition = definition
        return self._definition

    def load_prototype(self, definition):
        proto = definition.prototype
        proto_def = None
        if self.namespace is None:
            if proto.namespace is None:
                minfo = self.project.metainfo.get('extension') or {}
                if self.name not in minfo:
                    raise Exception(f"the definition required prototype not found")
                path = minfo.get('path') or f'extension/{self.name}'
                path = os.path.join(self.project.dir, path)
                if not os.path.exists(path, 'extension.yml'):
                    raise Exception('prototype in package not implemented')
                proto_def = Definition(path, where='package')
            else:
                proto_def = Definition.load(self.name, self.namespace, self.project, self.workbench)

        else:


    def exec(self, runner=None, argv=[]):
        from epm.tools.extension import Extension

        if self.definition.kind == 'prototype':
            raise Exception('prototype of extension is not runnable.')
        if self.definition.prototype:
            Prototype = self.load_prototype(self.definition.prototype)
            extension = Prototype(self.definition)

        else:
            extension = Extension(self.definition)


        #extension = Extension(self.definition)
        return extension.exec(argv, runner)





