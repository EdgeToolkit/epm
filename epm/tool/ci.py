import yaml

_DEFALT_CONFIG = '''
  settings:
    arch: [x86_64, x86]
    build_type: [Release, Debug]
'''


# scheme, compiler, version, arch, toolchain, runtime, build_type
from collections import namedtuple


class Job(object):
    KEYS = ['scheme', 'compiler', 'version', 'arch', 'build_type', 'toolchain', 'runtime']

    def __init__(self, compiler, scheme, version, arch, build_type, test, toolchain=None, runtime=None):
        self.scheme = scheme
        self.compiler = compiler
        self.version = version
        self.arch = arch
        self.build_type = build_type
        self.toolchain = toolchain
        self.runtime = runtime
        self.test = test

    def as_dict(self):
        value = {'test': self.test}
        for i in self.KEYS:
            value[i] = getattr(self, i)
        return value


class Matrix(object):
    _jobs = []

    def __init__(self, manifest, default=None):
        self._mainifest = manifest
        test = ['${sandbox}/%s' % x for x in manifest.get('sandbox', {}).keys()]

        scheme = list(set(manifest.get('scheme', {}).keys()) | {'default'})
        self._scheme = scheme

        self._default = {
            'arch': ['x86_64', 'x86'],
            'build_type': ['Release', 'Debug'],
            'scheme': scheme,
            'test': test,
        }
        self._default.update(default or {})

        ci_config = manifest.get('ci-config', {})
        self._libcxx = ci_config.get('libcxx', ['c++', 'c++11'])
        if isinstance(self._libcxx, str):
            self._libcxx = [self._libcxx]

        self._config = {'MSVC': [], 'GCC': []}

        for name in ['MSVC', 'GCC']:
            default = dict(self._default)
            if name == 'MSVC':
                default = dict(default, runtime=['MD'])
            if name == 'GCC':
                default = dict(default, toolchain=[None])

            for config in ci_config.get(name, []):

                c = dict(default, **config)
                for k, v in c.items():
                    if isinstance(v, list):
                        continue
                    c[k] = [v]
                self._add_job(name, c)

    @property
    def libcxx(self):
        return self._libcxx

    def _add_job(self, compiler, config):
        for scheme in config['scheme']:
            for version in config['version']:
                for arch in config['arch']:
                    for build_type in config['build_type']:
                        for toolchain in config.get('toolchain', [None]):
                            for runtime in config.get('runtime', [None]):
                                job = Job(compiler=compiler, scheme=scheme, version=version,
                                          arch=arch, build_type=build_type,
                                          test=config['test'],
                                          runtime=runtime,
                                          toolchain=toolchain)
                                if not self.has_job(job):
                                    self._jobs.append(job)

    def has_job(self, job):
        for j in self._jobs:
            exists = True
            for i in Job.KEYS:
                if getattr(job, i) != getattr(j, i):
                    exists = False
                    break
            if exists:
                return True
        return False

    def items(self, key):
        it = set()
        for j in self._jobs:
            it.add(getattr(j, key))
        it = list(it)
        it.sort()
        return it

    def job(self, compiler, scheme, version, arch, build_type, toolchain=None, runtime=None):
        for j in self._jobs:
            if j.compiler != compiler:
                continue
            if j.scheme != scheme:
                continue
            if j.version != version:
                continue
            if j.arch != arch:
                continue
            if j.compiler != compiler:
                continue
            if j.build_type != build_type:
                continue

            if runtime and j.runtime != runtime:
                continue

            if j.toolchain != toolchain:
                continue
            return j

        return None

    def table(self, prefix=''):
        table = []
        for key in Job.KEYS:
            n = len(key)
            for i in self.items(key):
                if isinstance(i, str):
                    if len(i) > n:
                        n = len(i)
            table += [(key, n)]

        title = '{}'.format(prefix)
        separator = '{}'.format(prefix)
        formater = '{prefix}'
        for k, l in table:
            fm = "| {0:%d} " % l
            title += fm.format(k)
            formater += "| {%s:%d} " % (k, l)
            separator += "+ %s " % ('-'*l)

        formater += '\n'
        tline = '{}{}'.format(prefix, '='*len(title))
        txt = "{}\n{}\n{}\n".format(tline, title, separator)
        for j in self._jobs:
            txt += formater.format(compiler=j.compiler, scheme=j.scheme, version=j.version,
                                   arch=j.arch, build_type=j.build_type,
                                   toolchain=str(j.toolchain), runtime=str(j.runtime),
                                   prefix=prefix)

        return txt

    @staticmethod
    def load(filename, default=None):
        manifest = filename
        if isinstance(filename, str):
            with open(filename) as f:
                manifest = yaml.safe_load(f)

        if isinstance(default, str):
            default = yaml.safe_load(default)
        return Matrix(manifest, default)






#############################################################################################



class Config(object):

    def __init__(self, manifest, default=None):
        self._mainifest = manifest
        test = ['${sandbox}/%s' % x for x in manifest.get('sandbox', {}).keys()]

        scheme = list(set(manifest.get('scheme', {}).keys()) | {'default'})
        self._scheme = scheme

        self._default = {
            'arch': ['x86_64', 'x86'],
            'build_type': ['Release', 'Debug'],
            'scheme': scheme,
            'test': test,
        }
        self._default.update(default or {})

        ci_config = manifest.get('ci-config', {})
        self._pure_c = ci_config.get('pure-c', False)
        self._libcxx = ci_config.get('libcxx', ['c++', 'c++11'])
        if self._pure_c:
            self._libcxx = []

        self._config = {'MSVC': [], 'GCC': []}

        for name in ['MSVC', 'GCC']:
            default = dict(self._default)
            if name == 'MSVC':
                default = dict(default, runtime=['MD'])
            if name == 'GCC':
                default = dict(default, toolchain=['None'])

            for config in ci_config.get(name, []):
                for k in config.keys():
                    if isinstance(config[k], list):
                        continue
                    config[k] = [config[k]]

                config = dict(default, **config)
                for i in config.keys():
                    if isinstance(config[i], list):
                        config[i] = [str(x) for x in config[i]]
                self._config[name].append(config)

    @property
    def purec(self):
        return self._pure_c

    @property
    def libcxx(self):
        return self._libcxx

    @property
    def scheme(self):
        return self._scheme

    def versions(self, compiler):
        return [x for x in self._config.get(compiler, {}).keys()]

    def match(self, compiler, version=None, arch=None, build_type=None, scheme=None,
              runtime=None, toolchain=None):

        candidates = self._config.get(compiler, [])

        condition = {'arch': arch, 'build_type': build_type, 'scheme': scheme,
                     'runtime': runtime, 'toolchain': toolchain, 'version': version}

        result = []
        for candidate in candidates:

            config = dict(candidate)
            match = True
            for key, value in condition.items():
                if value is None:
                    continue
                value = value if isinstance(value, list) else [value]
                value = list(set(value) & set(config.get(key, [])))
                if value:
                    config[key] = value
                    continue
                match = False
                break

            if match:
                result.append(config)
        return result

    @staticmethod
    def keys(configs, key):
        result = set()
        for c in configs:
            result |= set(c.get(key, []))
        result = list(result)
        return result

    @staticmethod
    def load(filename, default=None):
        manifest = filename
        if isinstance(filename, str):
            with open(filename) as f:
                manifest = yaml.safe_load(f)

        if isinstance(default, str):
            default = yaml.safe_load(default)
        return Config(manifest, default)

    @staticmethod
    def msyear(version):
        _visuals = {'8': '2005',
                    '9': '2008',
                    '10': '2010',
                    '11': '2012',
                    '12': '2013',
                    '14': '2015',
                    '15': '2017',
                    '16': '2019'}
        return _visuals.get(version, None)

    def __str__(self):
        return yaml.safe_dump(self._config, default_flow_style=False)

