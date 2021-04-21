#!/bin/bash
set -e
set -x
_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

BASE_GCC=( base-gcc5 base-gcc6 base-gcc7 base-gcc8 base-mingw )
LINARO_ARMV7=(linaro-gcc5-armv7 linaro-gcc6-armv7 linaro-gcc7-armv7 linaro-gcc8-armv7)
LINARO_ARMV8=(linaro-gcc5-armv8 linaro-gcc6-armv8 linaro-gcc7-armv8 linaro-gcc8-armv8)
X86_64=(gcc5 gcc6 gcc7 gcc8)
ARMV7=( gcc5-armv7 gcc6-armv7 gcc7-armv7 )
ARMV8=( gcc5-armv8 gcc6-armv8 gcc7-armv8 )

__CONAN_VERSION__=1.35.1

cd ${_DIR}/..
[ ! -d .epm ] && mkdir -p .epm
sudo rm -f .epm/epm.tar.gz 
git archive --format=tar.gz --output .epm/epm.tar.gz HEAD

function build_base_and_linaro()
{
   for i in ${BASE_GCC[*]} ${LINARO_ARMV7[*]} ${LINARO_ARMV8[*]}
   do
        sudo -E ./docker/main.py --build $i
   done
}

function build_epm()
{
   for i in ${X86_64[*]} ${ARMV7[*]} ${ARMV8[*]} 
   do
       sudo -E ./docker/main.py --build $i --version latest
   done
}


function tag_linaro() {    
    prefix=$1
    conan_version=$2
    [[ -z $conan_version ]] && conan_version=1.34.0
    if [[ -n $prefix ]]; then
       for i in ${LINARO_ARMV7[*]} ${LINARO_ARMV8[*]}
       do
         sudo docker tag edgetoolkit/${i}:$conan_version ${prefix}edgetoolkit/${i}:$conan_version     
       done
    fi
}


function tag_epm() {    
    prefix=$1
    conan_version=$2
    [[ -z $conan_version ]] && conan_version=$__CONAN_VERSION__
    if [[ -n $prefix ]]; then
       for i in ${X86_64[*]} ${ARMV7[*]} ${ARMV8[*]}
       do
         sudo docker tag edgetoolkit/${i}:latest ${prefix}edgetoolkit/${i}:latest
       done
    fi
}


function pub()
{
    prefix=$1
    conan_version=$2
    [[ -z $conan_version ]] && conan_version=$__CONAN_VERSION__
    for i in ${BASE_GCC[*]} ${LINARO_ARMV7[*]} ${LINARO_ARMV8[*]}
    do
        sudo docker tag edgetoolkit/${i}:$conan_version ${prefix}edgetoolkit/${i}:$conan_version
        sudo docker push ${prefix}edgetoolkit/${i}:$conan_version
        sudo docker rmi ${prefix}edgetoolkit/${i}:$conan_version
    done

    for i in ${X86_64[*]} ${ARMV7[*]} ${ARMV8[*]}
    do
        sudo docker tag edgetoolkit/${i}:latest ${prefix}edgetoolkit/${i}:latest
        sudo docker push ${prefix}edgetoolkit/${i}:latest
        sudo docker rmi ${prefix}edgetoolkit/${i}:latest
    done
}


function main()
{
    prefix=$1
    [[ -z $prefix ]] && prefix='172.16.0.119:8482/'
    build_base_and_linaro
    build_epm
    pub $prefix
}

main $*

