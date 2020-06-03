





<img src="./logo.png" width=64 height=64/> **Embedded-system package manager for C/C++ development base on [conan](conan.io) and [docker](https://docker.com).**

------

check website for details [epmkit.github.io/epm](https://epmkit.github.io/epm).



## Introduction

EPM is an embedded-system package manager base on [Conan](https://conan.io/) and [Docker](https://docker.com/), intended for C/C++ development team, and extends utilities to manage build, test, document and continuous integration to improve team development efficiency and quality.

EPM , is inspired by [npm](npmjs.org) ([Node.JS](nodejs.org) package manager),  uses meta-information manifest ( package.yml) to manipulate development activities of the package project.

EPM can be use to :

- create project skeleton.
- all conan features (building, cache, publish package ...)
- run built program in sandbox no need to set dependent dynamic libraries paths
- a command to generate CI configure file to avoid complicated configure.
- collaborate with Gitlab (via .gitlab-ci.yml) to easy continuous integration
- manage versioning document of Markdown by underlying [MKdocs](https://www.mkdocs.org/) .



## Setup

please read [installation guide.](./docs/installation.md)

## Your first EPM project

If  EPM installed successfully, type following command to verify your installation

```bash
$ epm --version
EPM 0.1.0
```

Now let's make your epm project step by step.

### Create package project

Let create an application program with name HelloWorld.

```shell
C:\>mkdir Hello

C:\>cd Hello

C:\Hello>epm project gen --name HelloWorld
app package <HelloWorld> project created successfully.
To build project, run command:  epm -c vs2019 build
```

After creation, you can find some folders and files under this directory. Open `source/main.c` you will see

```C
#include <stdio.h>

int main( int argc, char** argv )
{
    printf("HelloWorld 0.0.1\n");
    return 0;
}
```



### Build package

```shell

C:\Hello>epm --profile vs2019 build
[configure ......]
Configuration:
[settings]
arch=x86_64
arch_build=x86_64
build_type=Release
compiler=Visual Studio
compiler.runtime=MD
compiler.version=16
os=Windows
os_build=Windows
[build ......]
Using lockfile: 'C:\Hello\.epm\vs2019\build/conan.lock'
Using cached profile from lockfile
conanfile.py (HelloWorld/0.0.1@epm-public/dev): Running build()
-- Selecting Windows SDK version 10.0.17763.0 to target Windows 10.0.18362.
-- The C compiler identification is MSVC 19.23.28106.4
  main.c
  HelloWorld.vcxproj -> C:\Hello\.epm\vs2019\build\bin\HelloWorld.exe
  Building Custom Rule C:/Hello/CMakeLists.txt
  CMake does not need to re-run because 
[install ......]
  -- Install configuration: "Release"
  -- Installing: C:/Hello/.epm/vs2019/package/bin/HelloWorld.exe

[package testing  ......]
Using layout file: C:\Hello\.epm\vs2019\conan.layout

HelloWorld/0.0.1@epm-public/dev (test package): Installing package
Requirements
    HelloWorld/0.0.1@epm-public/dev from user folder - Editable
Packages
    HelloWorld/0.0.1@epm-public/dev:3fb49604f9c2f729b85ba3115852006824e72cab - Editable

HelloWorld/0.0.1@epm-public/dev (test package): Running build()
HelloWorld/0.0.1@epm-public/dev (test package): Running test()

```

### Run the built package

```bash
C:\Hello>epm -c vs2019 sandbox HelloWorld
HelloWorld 0.0.1
```





## Development

test

nosetests epm.test --with-summary-report --summary-report-on class



You set environment EPM_DEBUG_CONFIG_FILE to the path of debug config (with yaml format)

```yaml
profile:
  gcc5:
    docker:
      builder:
        image: epmkit/gcc5:debug
        epm:
          source: D:\epmkit\epm\epm
          target: /home/conan/.cache/epm/epm
```

above config will use epmkit/gcc5:debug instead of the origin images defined in profiles.

## Contribution



## License

project base on [conan](conan.io), and some code ported from GStreamer cerbero project, so the license should  adhere to them.

[MIT License](./LICENSE.md)

https://blog.conan.io/2016/03/22/From-CMake-syntax-to-libstdc++-ABI-incompatibiliy-migrations-are-always-hard.html