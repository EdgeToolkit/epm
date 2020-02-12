# Sandbox



## control the sandbox script with environment variables



### EPM_SANDBOX_PROJECT 

directory of the project where placed package.yml and conanfile.py



### EPM_SANDBOX_STORAGE

directory of the conan cache storage  path.

by default it equal to %CONAN_STORAGE_PATH%, if CONAN_STORAGE_PATH not set, EPM will use ~/conan/data as the value of conan storage path (which use to cache package create from local or download from remote)

### EPM_SANDBOX_RUNNER

format (auto|shell|docker)

specified which kind of runner to execute the program - shell, docker or remote device

for x86 and x86_64 host system, when **EPM_SANDBOX_RUNNER** set as auto/shell/docker , the behavior as below.

* Windows

  Host system is windows, second and third columns, the build target (for Windows or Linux) . N/A 

  | EPM_SANDBOX_RUNNER | Windows | Linux  | comments |
  | ------------------ | ------- | ------ | -------- |
  | auto               | shell   | docker |          |
  | shell              | shell   | N/A    |          |
  | docker             | N/A     | docker |          |

  

* Linux

    

  | EPM_SANDBOX_RUNNER | Windows | Linux        | comments                                                     |
  | ------------------ | ------- | ------------ | ------------------------------------------------------------ |
  | auto               | N/A     | docker/shell | if docker installed and startup, use docker first, otherwise try shell. There is potential problem that host c/c++ runtime is not work for the program. |
  | shell              | N/A     | shell        |                                                              |
  | docker             | N/A     | docker       |                                                              |

### EPM_SANDBOX_REMOTE

this var only valid for non x86/x86_64 CPU. armv7...

remote device name list (split by ;), any name that not configured in EPM register file will be ignored.

if this not set, random device will be selected.



### EPM_SANDBOX_IMAGE

* This was only valid when runner is docker. if the runner is docker, docker will use this specified image instead of the one configured in profile.

### EPM_SANDBOX_SHELL

This was only valid when runner is docker. if the runner is docker, docker will use this specified shell instead of the one configured in profile.







| Host    | Target |      |
| ------- | ------ | ---- |
| Windows |        |      |
|         |        |      |
|         |        |      |





## advance



### mount



host project dir => $home/@host/project

​        conan_storage                         /conan.storage