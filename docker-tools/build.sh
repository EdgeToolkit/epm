#!/bin/bash
_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

target=(gcc5 gcc5-x86 gcc8 gcc8-x86)
for i in ${target[*]}
do
 python3 .script/build.py ${i} --build --clear

done