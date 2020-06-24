







# scheme

scheme 部分定义了，包编译的配置选项，如果动态库，静态库等，具体选项会定义在conanfile.py 中options 基本格式

```yaml
scheme:
  <scheme type1>:
   options:
     shared: true
   <dep package1>: <the dep package1 scheme name>
   <dep package2>: <the dep package2 scheme name>
```

条件规则:

```yaml
scheme:
   default:
     options:
       shared: false
     zlib:
     - dynamic:
       - compiler: Visual Studio
     - static:
       - compiler: gcc
       - compiler.version: 5
```

