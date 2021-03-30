@ECHO OFF
pushd %~dp0\..
mkdir .epm
git archive --format=tar.gz --output .epm/epm.tar.gz HEAD
echo ./docker/main.py %*
python ./docker/main.py %*
popd
