#!/bin/bash
_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${_DIR}/..
[ ! -d .epm ] && mkdir -p .epm
git archive --format=tar.gz --output .epm/epm.tar.gz HEAD
echo sudo -E ./docker-tools/main.py $*
