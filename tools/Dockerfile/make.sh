#!/bin/bash
set -e

__DIR=$(cd `dirname $0`; pwd)

_python='python'
if [ $(uname) = "Linux" ]; then
    _python='sudo python3'
fi

CONAN_VERSION='1.24.0'
VERSION='latest'
options="--conan_version $CONAN_VERSION"
options="--pypi http://172.16.192.169:8040/repository/pypi/simple $options"
options="--http_proxy http://172.16.0.8888 $options"
options="--archive_url http://172.16.0.119/archive/ $options"
options="--build $options"
options="--clear $options"

$_python $__DIR/make.py conan-gcc5-x86 --version $CONAN_VERSION $options
$_python $__DIR/make.py conan-gcc8-x86 --version $CONAN_VERSION $options
$_python $__DIR/make.py conan-hisiv300 --version $CONAN_VERSION $options

$_python $__DIR/make.py gcc5-x86 --version $VERSION $options
$_python $__DIR/make.py gcc5     --version $VERSION $options
$_python $__DIR/make.py hisiv300 --version $VERSION $options
