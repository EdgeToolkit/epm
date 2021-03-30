#!/bin/bash


#sudo -E docker run --rm \
#--name nasm_None_1609301905.1266499 \
# -v /home/edgetoolkit/workspace/oss/nasm:/home/conan/project \
# -v /home/edgetoolkit/.epm:/home/conan/.epm \
# -e EPM_DOCKER_IMAGE=edgetoolkit/gcc8 \
## -e EPM_DOCKER_CONTAINER_NAME=nasm_None_1609301905.1266499 \
## -e EPM_BANNER_DISPLAY_MODE=auto \
# -e EPM_WORKBENCH=base-devel \
# -w /home/conan/project \
#    edgetoolkit/gcc8 \
# /bin/bash -c "epm api create eyJQUk9GSUxFIjogImdjYzgiLCAiUlVOTkVSIjogInNoZWxsIn0="
#


sudo -E docker run --rm
 _image=$1          -i
 _project=$2        -p
 _workbench=$3      -w
 -c
