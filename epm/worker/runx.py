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
        if len(token) == 1:
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
                print(self.namespace, '#', self.name, self.builtin)
                if self.namespace in [None, '', 'epm'] and self.name in self.builtin:
                    home = f'~/.epm/.workbench/{self.workbench}' if self.workbench else '~/.epm'
                    ex_dir = abspath(f'{home}/.extension/epm/{self.name}')
                    shutil.copytree(self.builtin[self.name], ex_dir)
                    definition = Definition.load(self.name, self.namespace, self.project, self.workbench)
                else:
                    raise e
            self._definition = definition
        return self._definition

    def exec(self, runner=None, argv=[]):
        path = os.path.join(self.definition.attribute.dir, self.definition.entry)
        from epm.utils import load_module
        m = load_module(path)
        if 'Main' not in dir(m):
            raise Exception('Illegal entry file, miss class Main')
        extension = m.Main(self.definition)
        return extension.exec(argv=argv, runner=runner)






