# Welcome {{ name }}

This is a [epm project](https://epmall.github.io/epm/project/)  of C/C++ {{ 'program' if type == 'app' else 'library'}}.

The major features of {{ name }}:

* feature1

  XXXXXX

* feature2

  XXXXXX

  

## Developer Guide
more details please refer to [epm documents](https://epmkit.github.io/epm).

## How to build

Make sure you have successfully [installed epm](https://epmkit.github.io/epm/installation).

To build Windows with VS2019

```bash
epm -c vs2019 build
```

or create package an cache in local machine with `create` to share other package/project, 

```bash
epm -c vs2019 create
```

you can also build for Linux system with `build` and `create` command, for example 

```bash
cpm -c gcc5 build
```


## How to run built artifacts

{% if  type == 'app' %}

* run the built program (in **sandbox**)

  ```
  epm -c vs2019 sandbox {{ name }}
  ```

  

* run unit tests for the built program (with Python Unittest see ./test_package/test_*.py)

  ```shell
  epm -c vs2019 run test
  ```

  

{% else %}

- run the test  program of {{ name }} library (in **sandbox**)

  ```
  epm -c vs2019 sandbox test_package
  ```

  

{% endif %}

## Generate gitlab ci config file

```
epm run gitlab-ci
```

Above command will generate .gitlab-ci.yml config file for Gitlab, you can modify ./script/gitlab-ci.py as you want.



## Verify document

Markdown template files has been generated in [docs](./docs) folder, and it will be publish automatically according your gitlab-ci rules.

You can verify the documents with `mkdocs` built-in webserver, for example

```sh
$ mkdocs serve
```

or built a site files

```bash
$ mkdocs build
```



