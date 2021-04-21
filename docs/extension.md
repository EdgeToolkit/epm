

# 扩展(eXtension)



EPM 扩展(extension)为用户提供了自定义的CLI入口通过命令行方式执行 epm runx <extension name> [args ...]。

扩展通过安装在可以使用(buildin除外)，扩展可以被安装在当前项目目录下，工作台(workench),全局。扩展的搜索顺序也就是 `当前目录`-> `工作台`->`全局`

## 安装

```
epmx install github.com/xxxx/yyy@version  --as xxxxx --global --workbench
```

epmx gitlab.com/xxx/yyy --help

epmx list --workbench --global --all

epmx 

epmx gitlab.com/xxx/yyy --help





epm.API

epm.Extension

from epm import Extension

args.yml

main.py

extension.yml

```
name: xxx

```



epm.tools







## 扩展定义文件格式(draft)

```yaml

extension:
  [xxxx]/extension.yml
  __builtin__/xxxx
  <namespace>/<name>/<version>|_/extension
---
name: mkprj
namespace: epm
version: 0.0.1
url: git+https://github.com/edgetoolkit/epm.git@{{prototype.version}}#extension/mkprj

description: |
  扩展(原型)定义模版
author: Mingyi Zhang
email: mingyi.z@outlook.com
home: https://github.com/edgetoolkit/epm/extension/mkprj
url: git+https://github.com/edgetoolkit/epm@x
url: git+https://github.com/edgetoolkit/epm.git@${__version__}#extension/mkprj
topics: [C/C++, generate, project]
license: MIT
entry: main.py

```

epm extension install  X --global/workbench/

epm extension remove  X 

epm --profile --scheme --runner runx github.com/mingyiz/epx:hello   

epx --profile --scheme --runner github.com/mingyiz/epx:hello



extension.yml 

```yaml
extension:
  .config:
     namespace:
        github.com/edgetoolkit/epm/uuyy:
        ................................
   mkprj:
     location: extension/mkprj
```

