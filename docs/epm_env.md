# EPM_ENV

epm tools is able to overwrite your package.yml config with environment configure file. Please read [Gitlab-Flow@epm](./gitlab-flow.md) so that you can have a good understanding of the below discussion.



## Channel definition rules

*what's environment configure will explain in later section, please focus on channel definition rule in this part.*

As [conan](conan.io)'s rules - package is identified by reference `name`/`version`@`user`/`channel`, In epm we have explicitly defined the user in package.yml, but what's channel? 

In epm the default policy is stable branch released to `stable` channel, master released to `testing` channel, and others in `dev` channel. This solution works, but we have to change channel configuration before MR or after MR , since the dependent package may released on `Master` or `Stable` branch. 

To reduce more change works on Git source file, let's make an appointment that package defined channel plan and can be overwritten by epm environment configure. the rule is

* If epm environment configure defined the specified package channel, the channel is set as it (whatever defined in package.yml or not)
* if environment configure not defined, use package.yml definition.
* Neither environment configure nor package.yml defined the package channel, then channel set as `stable`. 

for example:

```yaml
# package.yml

dependencies:
  libA:
    user: epm
    version: 0.1.0
    channel: testing
  libB:
    user: epm
    version: 1.1.0
  
```



if we only defined libA channel is `dev` in environment configure, then the building will use following reference for this package

 libA/0.1.0@ epm/`dev`    libB/1.1.0@epm/`stable`

if there is no any channel definition in environment configure, the references are

 libA/0.1.0@ epm/`testing`    libB/1.1.0@epm/`stable`



## Environment configure

environment configure are defined in YAML format files, you may find global in ~/.epm/env (or windows %USERPROFILE%/.epm/env) folder. and local one in your project with name foramt ${name}.epm_env.yml, the ${name} is environment name for example production.epm_env.yml.

epm will load the configure according environment variable **EPM_ENV**, if the EPM_ENV is set to production we will try your project first, if your local project have no  production.epm_env.yml, we will find the global folder, error will be raised if not find in both place.

```yaml

packages:
   libA:
     0.0.9: dev
     0.1.0: stable
   libB: testing
```

To ways defined, overwrite specified version (libA), overwrite all (libB)