# 可执行程序（program）

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

如果`program.location` 项没有定义，者说明该可执行程序是包构建过程生成的应用程序。那么executable 的的定位遵循以下规则

* 搜索构建目录的package目录

* 搜索包构建目录的build目录

* 搜索包构建目录

  对于build 和create 包的构建目录是不同的





