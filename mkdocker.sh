python3 tools/mkdocker.py conan-gcc5-x86 --version 1.24.0 --build --config tools/docker/config.yml
python3 tools/mkdocker.py conan-gcc8-x86 --version 1.24.0 --build --config tools/docker/config.yml
python3 tools/mkdocker.py conan-hisiv300 --version 1.24.0 --build --config tools/docker/config.yml
python3 tools/mkdocker.py hisiv300 --version latest --build --config tools/docker/config.yml
python3 tools/mkdocker.py gcc5-x86 --version latest --build --config tools/docker/config.yml
python3 tools/mkdocker.py gcc5 --version latest --build --config tools/docker/config.yml


