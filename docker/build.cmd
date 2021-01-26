@ECHO OFF
pushd %~dp0\..
mkdir .epm
git archive --format=tar.gz --output .epm/epm.tar.gz HEAD
echo ./docker-tools/main.py %*
python ./docker-tools/main.py %*
popd
