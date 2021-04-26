
import unittest
from epm.tools.files import save
from epm.tools.decorater import chdir

from epm.model.project import Project


_METAINFO_MANIFEST='''
name: test1
version: 1.2.3

test:
  test_package:
  p1:
    program: P1
  p2:
    project: test_p2
  p3:
    args: a b c
  p4:
    program: P4
    project: P4dir
    args: 1 2 3

'''


class TestProjectMetaInfo(unittest.TestCase):
    
    @chdir('test.model.project.metainfo')
    def test_basic(self):
        save(_METAINFO_MANIFEST, 'package.yml')
        project = Project(None, None)
        
        self.assertEqual('test1', project.name)
        self.assertEqual('1.2.3', project.version)
        
        test = project.test['test_package']
        self.assertEqual('test_package', test.name)
        self.assertEquals(None, test.project)
        self.assertEqual('test_package', test.program)
        self.assertEqual('', test.args)
        self.assertEqual('', test.description)
        
        test = project.test['p1']
        self.assertEqual('p1', test.name)
        self.assertEquals(None, test.project)
        self.assertEqual('P1', test.program)
        self.assertEqual('', test.args)
        self.assertEqual('', test.description)
        
        test = project.test['p2']
        self.assertEqual('p2', test.name)
        self.assertEquals('test_p2', test.project)
        self.assertEqual('p2', test.program)
        self.assertEqual('', test.args)
        self.assertEqual('', test.description)
        
        test = project.test['p3']
        self.assertEqual('p3', test.name)
        self.assertEquals(None, test.project)
        self.assertEqual('p3', test.program)
        self.assertEqual('a b c', test.args)
        self.assertEqual('', test.description)

        test = project.test['p4']
        self.assertEqual('p4', test.name)
        self.assertEquals('P4dir', test.project)
        self.assertEqual('P4', test.program)
        self.assertEqual('1 2 3', test.args)
        self.assertEqual('', test.description)
        
        