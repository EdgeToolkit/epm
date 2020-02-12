docker run -d --name epm.test.conan_server -p 9300:9300 -v %~dp0\server.conf:/root/.conan_server/server.conf -v %~dp0\data:/root/.conan_server/data conanio/conan_server

docker ps -a
pause
