#!/bin/bash

__DIR=$(cd `dirname $0`; pwd)

_SUDO=''
_clear_exited_conatainer='docker rm $(docker ps -q -f status=exited)'
_python='python'
if [ $(uname) = "Linux" ]; then
    _SUDO='sudo'
    _python='python3'
    _clear_exited_conatainer='sudo docker rm $(sudo docker ps -q -f status=exited)'
fi
echo $_clear_exited_conatainer
#$_clear_exited_conatainer

CONAN_VERSION='1.24.0'
VERSION='latest'
options="--conan_version $CONAN_VERSION"
options="--pypi http://172.16.192.169:8040/repository/pypi/simple $options"
options="--http_proxy http://172.16.0.119:8888 $options"
options="--archive_url http://172.16.0.119/archive/ $options"
options="--build $options"
#options="--clear $options"

#CONAN_IMAGES=(conan-gcc5-x86 conan-gcc8-x86 conan-hisiv300)
EPM_IMAGES=(gcc5-x86 gcc5 hisiv300)




for target in ${CONAN_IMAGES[@]};
do
  $_SUDO docker rmi $target:$CONAN_VERSION
done

for target in ${EPM_IMAGES[@]};
do
  $_SUDO docker rmi $target:$VERSION
  
done

set -e

for target in ${CONAN_IMAGES[@]};
do
  $_SUDO $_python $__DIR/make.py  $target --version $VERSION $options
done


for target in ${EPM_IMAGES[@]};
do
  $_SUDO $_python $__DIR/make.py  $target --version $VERSION $options
done
