



mount rules



${HOME}/@host/epm <源码位置>

${HOME}/@host/.epm <主机epm工作位置>

${HOME}/@host/project/ <主机项目工作位置>

${HOME}/@sandbox/  ln-s

\bin

\lib

\







```python
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
以root权限执行，注意su和sudo依赖于终端，所以必须在终端下执行
"""

import os
import sys


if __name__ == '__main__':
    # 提升到root权限
    if os.geteuid():
        args = [sys.executable] + sys.argv
        # 下面两种写法，一种使用su，一种使用sudo，都可以
        os.execlp('su', 'su', '-c', ' '.join(args))
        # os.execlp('sudo', 'sudo', *args)

    # 从此处开始是正常的程序逻辑
    print('Running at root privilege. Your euid is', os.geteuid())
```







## debug configuration

You specify debug config file path in  enviroment var `EPM_DEVELOP_CONFIG` to enable debug configuration.

The debug config is a file with format YAML

```yaml
profile:
  gcc5: # scheme failimay name
    docker: 
      builder:
        image: epmkit/gcc5:debug
        epm:
          source: /home/mingyiz/epmkit/epm
          target: /mnt/epm
```

