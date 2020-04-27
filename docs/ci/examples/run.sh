#!/usr/bin/env bash
currentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${currentDir}/conf/${1}.sh
_localhost=${2}
_script=${3}
_step=${4}

if [ ${_step} == 'build_script' ]; then
script=$(cat ${_script})
sshpass -p ${_CI_SSH_PASSWORD} ssh -p ${_CI_SSH_PORT} admin@${_CI_HOSTNAME} -o StrictHostKeyChecking=no << EOF
umount -f ${_CI_BUILDS_DIR} >/dev/null 2>&1
[ ! -d ${_CI_BUILDS_DIR} ] && mkdir -p ${_CI_BUILDS_DIR}
mount -t nfs -o nolock ${_localhost}:${_CI_BUILDS_DIR} ${_CI_BUILDS_DIR}
export EPM_SANDBOX_RUNNER=shell
/bin/sh -c ${script}
EOF

else
  export PATH=/home/epm:$PATH
  /bin/bash ${_script}
fi

