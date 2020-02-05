#!/bin/bash
_WD=$(cd $(dirname "${BASH_SOURCE[0]}"); $PWD)

if [[ -n $EPM_VENV_NAME ]] ;; then
  echo "Already in virtual environment <%EPM_VENV_NAME%>, you have to exits this venv, then try again."
  exit/b 1
fi

export EPM_VENV_NAME={{name}}
export EPM_VENV_DIR={{path}}
export CONAN_USER_HOME=${EPM_VENV_DIR}
export EPM_USER_HOME=${EPM_VENV_DIR}
export EPM_CHANNEL={{ channel }}

python venv.py
