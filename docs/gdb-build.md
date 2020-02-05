

# Window GDB Client (Build with MSys2 Mingw32)



install http://repo.msys2.org/distrib/i686/msys2-base-i686-20190524.tar.xz

startup mingw32

```bash
$ pacman -S mingw-w64-i686-gcc
$ pacman -S make
$ pacman -S diffutils 
$ pacman -S texifnfo

export CFLAGS=-O2
export CXXFLAGS=-O2
export AR=/mingw32/bin/ar

CONFIG_OPTIONS='--disable-host-shared --with-static-standard-libraries --with-gmp=no --with-isl=no --with-gmp=no --with-mpf=no --with-mpc=no'

```



| Target | --host       | --target            | --program-prefix    | --program-suffix |
| ------ | ------------ | ------------------- | ------------------- | ---------------- |
| X86    | i686-mingw32 | i686-linux-gnu      | x86-linux-gnu       |                  |
| X86_64 | i686-mingw32 | x86_64-linux-gnu    | x86_64-linux-gnu    |                  |
| ARM    | i686-mingw32 | arm-linux-gnueabi   | arm-linux-gnueabi   |                  |
| ARM-hf | i686-mingw32 | arm-linux-gnueabihf | arm-linux-gnueabihf |                  |



* x86_64  Linux
  * --host=i686-mingw32   --target=x86_64-linux
* x86 Linux
* arm Linux
* 