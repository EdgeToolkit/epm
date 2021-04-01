@ECHO OFF
pushd %~dp0\..
mkdir .epm
git archive --format=tar.gz --output .epm/epm.tar.gz HEAD
python ./docker/main.py  --build %* 
popd
