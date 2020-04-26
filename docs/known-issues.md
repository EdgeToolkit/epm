





## Missing libs collection on build test step

When you running command `epm --profile xxx build --test`

if you simple write CMakeLists.txt  target link as below

```cmake
cmake_minimum_required(VERSION 2.8.11)
project(test_package C)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})
```

You will find the ${CONAN_LIBS} not include the lib of the target package.

and you may find an warning (here is the example of cjson)

```bash
cjson/1.7.12@epm/public: WARN: Lib folder doesn't exist, can't collect libraries: D:/EdgeOS/epm-oss/cjson\lib
```

The root cause is that build folder not in the package, could not find built libs

now, you have to solve it with following workaround

```cmake
add_executable(${PROJECT_NAME} test_package.c)
set(CONAN_LIBS cjson ${CONAN_LIBS}) # clear specified the libs
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})
```

