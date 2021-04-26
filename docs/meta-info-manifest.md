# 包信息定义文件 （package.yml）

epm 项目采用YAML格式的包定义文件，描述软件包构建，测试等元信息。



## 测试(程序)

### 格式

```yaml
test:
  test_package: # 测试程序信息定义
    project: # str [optional]
    program: # str 
    args: # str [optional]
```

测试程序信息定义部分可以是字符串或字典。

该字典的key定义了在沙盒(sandbox)中使用的助记名，其内容中的字段解释如下



* project [可选]

  该项为字符串，定义了该测试程序软件工程的目录， 如果该值未定义者表明测试程序是包内编译的可执行程序

* program  [必选]

  字符串格式，测试程序的文件名(Window下不含.exe)，搜索策略见

* args  [可选]

  运行该测试程序是默认待的参数



测试程序的搜索策略:

1. 通过 `create` 命令创建的

   

