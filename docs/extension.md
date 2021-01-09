



## 扩展定义文件格式

```
name:  [required] # 扩展名
version: 
prototype: 扩展原型，如定义将在 ~/.epm/extension/.protype 中寻找来加载本扩展定义，否则为自实现
kind: prototype| extension # default extension
description: [opt]
deps:
  pip: 
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

