# Install

EPM can be installed on Windows and Linux. for now, only Windows 10 and Ubuntu 18.04 had been verified. Ideally, it works on all the conan supported platforms.

EPM is a python package, so you can easily install with pip:

```bash
$ pip install epm
```

In ubuntu you may need use sudo  `sudo pip install epm`

**`IMPORTANT`** Please read below prerequisite software installation to ensure your building job works

# Prerequisite software

## Windows

* [Python](https://www.python.org/downloads/release) (>=3.6)

* [git-scm](https://www.git-scm.com/download/) 

  If you like graphic UI, you can have a try https://tortoisegit.org/download/

* [CMake](https://cmake.org/download/) (>= 3.10)  

* [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop) 

  Windows docker is only used when doing cross-building.

  Please read the installation guide https://docs.docker.com/docker-for-windows/install/

  HINT: read the `system requiurements` carefully.

  - Windows 10 64-bit: Pro, Enterprise, or Education (Build 15063 or later).
  - Hyper-V and Containers Windows features must be enabled.
  - The following hardware prerequisites are required to successfully run Client Hyper-V on Windows 10:
    - 64 bit processor with [Second Level Address Translation (SLAT)](http://en.wikipedia.org/wiki/Second_Level_Address_Translation)
    - 4GB system RAM
    - BIOS-level hardware virtualization support must be enabled in the BIOS settings. For more information, see [Virtualization](https://docs.docker.com/docker-for-windows/troubleshoot/#virtualization-must-be-enabled).

  

* [Visual Studio 2019](https://visualstudio.microsoft.com/downloads/)

  Other Visual Studio edition also supported, but you have to add profile manually in epm.

  

## Ubuntu

* 18.04

  * upgrade python to latest

    ```bash
    $ sudo apt update
    $ sudo apt upgrade python3
    $ sudo apt install python3-pip
    $ sudo sudo pip3 install --upgrade pip 
    ```

    

  * install docker

    ```bash
    $ sudo apt install docker.io
    ```

    