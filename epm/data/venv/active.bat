@echo off
if defined EPM_VENV_NAME (
  echo "Already in virtual environment <%EPM_VENV_NAME%>, you have to exits this venv, then try again."
  exit/b 1
)


set EPM_VENV_NAME={{name}}
set EPM_VENV_DIR={{path}}
set EPM_USER_HOME=%EPM_VENV_DIR%
set CONAN_USER_HOME=%EPM_VENV_DIR%

set EPM_CHANNEL={{ channel }}

epm venv banner

title [epm venv] - {{name}}
prompt $p [epm venv]@{{name}} $_$$
