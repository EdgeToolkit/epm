



## 扩展定义文件格式

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

