cat << EOS
{
  "builds_dir": "${_CI_BUILDS_DIR}",
  "cache_dir": "${_CI_CACHE_DIR}",
  "builds_dir_is_shared": true,
  "hostname": "_CI_HOSTNAME",
  "driver": {
    "name": "_CI_DRIVER_NAME",
    "version": "_CI_DRIVER_VERSION"
  }
}
EOS