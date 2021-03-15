# 包应用程序（Program of  the package）

为有效建议的测试验证包(C/C++库)，EPM提供了`program` 定义描述语法来定义一个C/C++的编译输出件。

`program` 描述的构建对象可能来源于包本身内部的编译 如 zlib库在构建时也可以生成 **minizip**， 另外也可能是用独立构建的项目(其依赖于该包)。

以zlib项目为例，

zlib构建时产生应用程序 minizip (windows: minizip.exe ), 该可执行程序位于 zlib编译包中， 同时我们也创建了test_package项目生成test可执行程序

其描述片段如下

```yaml
program:
- name: minizip
  executalbe: bin/minizip # 先搜package, 在build
- name: test_package
  project: test_package
  executable: bin/test_package
```





########################################

epm 提供了包相关集成工具，用于开发者构建可执行程序并方便验证包 - 可执行程序(program)

可执行程序在package.yml中定义如下

```yaml
program:
- name: test_package
  location: test_package
  executable: bin/test_package
```

如上内容定义了可执行程序，该程序的项目工程在test_package 目录中（其中包含conanfile.py等），通过编译构建将生成应用程序 test_package（或test_package.exe 在Windows）。test_package 的定位遵循以下规则

.epm/`<project.out>`/program/`test_package`/bin/test_package

如果`program.location` 项没有定义，则说明该可执行程序是包构建过程生成的应用程序。那么executable 的的定位遵循以下规则

* 搜索构建目录的package目录

* 搜索包构建目录的build目录

* 搜索包构建目录

  对于build 和create 包的构建目录是不同的





