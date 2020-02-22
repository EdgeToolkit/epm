# EPM Continuous Integration system deployment tool



# Deploy server



```bash
$ cd epm/ci/ansible
$ ansible-playbook -i HOSTS server.yml
```





# Appendix

## Query docker registry

Set URL as your registry location

* query all repository

  ```bash
  $ curl -k $URL/v2/_catalog
  {"repositories":["library/alpine"]}
  ```

  

* check docker volume repositories

  ```bash
  $ MOUNT_POINT=/var/lib/registry
  $ docker run -it --name check --rm -v ci_registry:$MOUNT_POINT  ubuntu /bin/bash -c "ls $MOUNT_POINT/v2/repositories/library -l -a"
  ```

  

* backup docker registry

  ```bash
  $ MOUNT_POINT=/var/lib/registry
  $ docker run -it --name backup --rm -v ci_registry:$MOUNT_POINT -v $PWD:/backup -w /backup  ubuntu /bin/bash -c "tar cvf registry.tar $MOUNT_POINT"
  
  ```

  

* docker run -d --name='tinyproxy' -p 8888:8888 dannydirect/tinyproxy:latest ANY

* 