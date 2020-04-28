# Environment variables

These are the environment variables used to customize EPM.



# EPM_GROUP, EPM_CHANNEL

In epm, we use group to replace the `user` of Conan.

These environment variables will be checked when using `self.user` or `self.channel` in package recipes (conanfile.py) in user space, where the user and channel have not been assigned yet (they are assigned when exported in the local cache). More about these variables in the [attributes reference](https://docs.conan.io/en/latest/reference/conanfile/attributes.html#user-channel) of conan.

If user not assigned `group` filed in package.yml, we will check the environment variable EPM_GROUP to set as $EPM_GROUP. 

If  `group` has been set in package.yml and EPM_GROUP_< `group` uppercase> exists, we will use this value as the package group final name. for example you have package.yml

```yaml
name: zlib
version: 1.8.1
group: epm
```

and the environment EPM_GROUP_EPM is 'new_epm', we will set conan user as 'new_epm'

EPM_CHANNEL is almost same, but EPM_GROUP_<group|upper> _CHANNEL _<channel x> will replace

EPM_GROUP_group_CHANNEL_channel

