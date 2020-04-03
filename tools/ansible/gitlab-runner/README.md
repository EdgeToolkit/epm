



builder.docker GItlab-CI Docker executor for builder (Linux)

builder.VS2019 Visual studio 



runner.docker

runner.windows



deployer.conan

deployer.doc





```bash
python _scripts/gitlab-runner-register.py -c _script/runner-config.yml -hosts HOSTS
```



Class A (Linux)

builder.docker

runner.docker

deployer.conan



Class B (Windows)

builder.VSxxx

runner.windows



class C 

deployer.doc



| Hostname       | Platform | docker | doc.publisher | builder | msbuilder | publisher | comments |
| -------------- | -------- | ------ | ------------- | ------- | --------- | --------- | -------- |
| 172.16.0.119   | Linux    |        | Y             |         |           |           |          |
| 172.16.192.169 | Linux    | Y      |               | Y (1)   |           | Y         |          |
| 172.16.192.241 | Linux    | Y      |               | Y (1)   |           | Y         |          |
| 172.16.192.238 | Windows  |        |               |         | Y (2)     |           |          |
| 172.16.192.238 | Windows  |        |               |         | Y (2)     |           |          |

| Runner         | Platform | executor     | G1   | G2   |
| -------------- | -------- | ------------ | ---- | ---- |
| docker         | Linux    | docker       | Y    |      |
| builder        | Linux    | docker       | Y    |      |
| msbuilder      | Windows  | shell.ps     |      | Y    |
| windows        | Windows  | shell dos/ps |      | Y    |
| doc.publisher  | Linux    | customer     |      |      |
| conan.deployer | Linux    | customer?    | Y    |      |
| edgeos.deveice | Linux    | customer?    |      |      |



* Linux
  * docker-excutor
    * `Linux` `docker` 
  * docker.builder (1)
    * `Linux`  `docker.builder`  
  * conan.deployor
    * conan.deployer
  * docman
    * `docman` 

* Windows

  * VIsual Studio 2019 builder (2)

    * `vs2019.builder`    

  * Windows runner

    * Windows

    
