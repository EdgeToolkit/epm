# 介绍



EPM是基于[Conan](https://conan.io/) 和 [Docker](https://docker.com)的嵌入式系统C/C ++开发的软件包管理器，并且扩展了很多实用工具程序来管理构建，测试，文档以及持续集成，以提高团队开发效率和质量。

EPM 的设计受到了Node.JS包管理工具NPM启发， 我们采用也了原信息配置文件(package.yml)来管控软件包开发活动。

EPM 可以协助你进行一下开发工作:

* create package (project) development skeleton.
* all conan features (building, cache, publish package ...)
* run built program in sandbox no need to set dependent dynamic libraries paths
*  a command to generate CI configure file to avoid complicated configure.
* collaborate with Gitlab (via .gitlab-ci.yml) to easy continuous integration
* manage versioning document of Markdown by underlying [MKdocs](https://www.mkdocs.org/) .



EPM is born for continuous integration, thus it well collaborates with CI/CD system. following is a typical application and deployment. 

![system overview](./images/system-overview.png)





