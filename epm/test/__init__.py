import os
import warnings



EPM_TEST_FOLDER = os.getenv('EPM_TEST_FOLDER', None)



# Enable warnings as errors only for `conan[s]` module

#warnings.filterwarnings("error", module="(.*\.)?conans\..*")