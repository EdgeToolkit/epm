

1. Sandbox 用于执行命令行的Sandbox

2. 用户Python脚本进行测试的

   ```python
   sandbox = Sandbox(project, name)
   sandbox.exec(argv, sync=True)
   sandbox.start(argv)
   
   ```

   