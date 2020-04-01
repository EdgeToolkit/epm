import os
import sys
import unittest

if __name__ == '__main__':
    
    pattern = "test*.py"
    if len(sys.argv) >2:
      pattern = sys.argv[2]
      
    cases = unittest.defaultTestLoader.discover(
    os.path.dirname(__file__), pattern=pattern,top_level_dir=None)

    runner = unittest.TextTestRunner()
    runner.run(cases)