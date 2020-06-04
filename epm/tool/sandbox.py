import os
import queue
import threading
import telnetlib
import paramiko
import time
import pathlib
import subprocess
from abc import ABC, abstractmethod
from time import monotonic as _time

from epm.api import API
from epm.model.project import Project
from epm.model.sandbox import HOST_FOLDER, PROJECT_FOLDER, CONAN_STORAGE, SANDBOX_FOLDER

from epm.util import system_info
PLATFORM, ARCH = system_info()


def trim(s, sep=b' \t\r\n'):
    n = len(s)
    begin = 0
    end = n
    while begin < n:
       if s[begin] in sep:
           begin +=1
       else:
          break

    while end:
       if s[end-1] in sep:
           end -=1
       else:
          break
    return s[begin:end]


def get_runner_config(profile, scheme, runner, api=None):
    import copy
    from epm.api import API
    if runner == 'shell':
        return {'.type': 'shell'}

    api = api or API()
    project = Project(profile, scheme, api)
    profile = project.profile

    if runner in [None, 'auto', 'docker']:

        docker = profile.docker.runner
        config = {'.type': 'shell'}
        if docker:
            config = {'.type': 'docker', 'docker': docker}
    else:
        sysconf = api.load_config()
        rc = sysconf.get('runner', {}).get(runner)
        if not rc:
            raise NameError('runner <{}> not exists'.format(runner))
        config = copy.deepcopy(rc)
        config['.type'] = 'runner'
        config['localhost'] = copy.deepcopy(sysconf.get('localhost', {}))

    if 'docker' in config:
        config['docker'] = dict({'home': '/tmp', 'shell': '/bin/bash'}, **config['docker'])

    if 'ssh' in config:
        config = dict({'home': '/tmp', 'shell': '/bin/bash'}, **config)

    return config


class _Shell(object):

    def __init__(self):

        self.encoding = 'utf-8'
        self._cache = b''
        self._binary_mode = True
        self._returncode = None
        self._polling_interval = 0.02
        self._start_time = None
        self._end_time = None
        self._startup_duration = None
        self._hostname = '127.0.0.1'
        self._localhost = '127.0.0.1'
        self._input = False

    @property
    def hostname(self):
        return self._hostname

    @property
    def localhost(self):
        return self._localhost

    @property
    def startup_duration(self):
        return self._startup_duration

    @abstractmethod
    def open(self, timeout=None):
        pass

    @abstractmethod
    def close(self):
        pass

    def _wait(self, timeout=None):
        if timeout is None:
            timeout = self._polling_interval
        time.sleep(timeout)

    def read(self, n=-1, timeout=None):
        buf = self._get(n)
        if len(buf) == n:
            return buf

        if timeout is not None:
            deadline = _time() + timeout

        while self.running:
            if self._sync():
                buf += self._get(n)
                if n == len(buf):
                    return buf

            if timeout is not None:
                timeout = deadline - _time()
                if timeout < 0:
                    break
            self._wait()
        return buf


    def read_until(self, match, timeout=None, check=False):
        """Read until a given string is encountered or until timeout.

        When no match is found, return whatever is available instead,
        possibly the empty string.  Raise EOFError if the connection
        is closed and no cooked data is available.
        if check set, raise TimeoutError when timeout

        """
        if self._binary_mode:
            if isinstance(match, str):
                match = bytes(match, encoding=self.encoding)

        n = len(match)
        i = self._find(match)
        if i >= 0:
            return self._get(i + n)

        if timeout is not None:
            deadline = _time() + timeout

        while self.running:
            begin = max(0, self._size() - n)
            if self._sync():
                i = self._find(match, begin)
                if i >= 0:
                    return self._get(i + n)

            if timeout is not None:
                timeout = deadline - _time()
                if timeout < 0:
                    break
            self._wait()

        if check:
            raise TimeoutError(self._get())
        return self._get()

    def expect(self, list, timeout=None, check=False):
        """Read until one from a list of a regular expressions matches.

        The first argument is a list of regular expressions, either
        compiled (re.RegexObject instances) or uncompiled (strings).
        The optional second argument is a timeout, in seconds; default
        is no timeout.

        Return a tuple of three items: the index in the list of the
        first regular expression that matches; the match object
        returned; and the text read up till and including the match.

        If EOF is read and no text was read, raise EOFError.
        Otherwise, when nothing matches, return (-1, None, text) where
        text is the text received so far (may be the empty string if a
        timeout happened).

        If a regular expression ends with a greedy match (e.g. '.*')
        or if more than one expression can match the same input, the
        results are undeterministic, and may depend on the I/O timing.

        """
        re = None
        list = list[:]
        indices = range(len(list))
        for i in indices:
            if not hasattr(list[i], "search"):
                if not re: import re
                pattern = list[i]
                if isinstance(pattern, str):
                    if self._binary_mode:
                        pattern = bytes(pattern, encoding=self.encoding)
                list[i] = re.compile(pattern)
        if timeout is not None:
            deadline = _time() + timeout

        first = True
        while self.running:
            if self._sync() or first:
                i, m, text = self._search(list)
                if text:
                    return i, m, text

            if timeout is not None:
                timeout = deadline - _time()
                if timeout < 0:
                    break
            self._wait()

        text = self._get()
        if check:
            raise TimeoutError(text)

        return -1, None, text

    @abstractmethod
    def exec(self, cmd, env=None):
        pass

    @abstractmethod
    def call(self, cmd, timeout=None, env=None, check=False):
        raise NotImplemented('call not implemented.')

    @abstractmethod
    def _sync(self):
        """ sync data from shell out buffer to cahce, and return the updated bytes.
        :return:
        """
        raise NotImplemented('_sync not implemented.')

    def _size(self):
        return len(self._cache)

    def _find(self, sub, start=None, end=None):
        return self._cache.find(sub, start, end)

    def _search(self, patterns):
        i = 0
        for pattern in patterns:
            m = pattern.search(self._cache)
            if m:
                e = m.end()
                text = self._get(e)
                return (i, m, text)
            i += 1
        return (-1, None, None)


    def _put(self, data):
        self._cache += data

    def _get(self, n=-1):
        """Try to pop the request count data, but the return data may less then request
        """
        if n > 0:
            n = min(len(self._cache), n)
            buf = self._cache[:n]
            self._cache = self._cache[n:]
        elif n < 0:
            buf = self._cache
            self._cache = b''
        else:
            buf = b''
        return buf

    @property
    def returncode(self):
        """command exited coded"""
        return self._returncode

    @property
    @abstractmethod
    def eof(self):
        return not self.running and not self._cache

    @property
    @abstractmethod
    def running(self):
        raise NotImplemented('exited not implemented.')

class Shell(_Shell):

    def __init__(self):
        super(Shell, self).__init__()
        self._proc = None

    def open(self, timeout=None):
        pass

    def close(self):
        if self._returncode is None and self._proc:
            self._proc.kill()
            self._proc = None

    def exec(self, cmd, env=None):
        self._startup_duration = None
        self._start_time = _time()
        self._returncode = None
        stdin = subprocess.PIPE #if self._input else None
        if env:
            env = dict(os.environ.copy(), **env)
        #print(cmd, stdin, subprocess.PIPE, env)
        with open(cmd, 'w') as f:
            data = f.read()
            data.replace('-it', '-t')
            f.write(data)
            f.close()
        subprocess.run(cmd, stdin=stdin, stdout=subprocess.PIPE, shell=True, env=env)
        import  sys
        sys.exit()
        return

        self._proc = subprocess.Popen(cmd, stdin=stdin, stdout=subprocess.PIPE, shell=True, env=env)
        for i in range(1, 100):
            self._sync()
            time.sleep(0.1)


    def call(self, cmd, env=None, timeout=None, check=False):
        self.exec(cmd, env)
        if timeout is not None:
            deadline = _time() + timeout

        while not self.eof:
            self._sync_cache()
            if timeout is not None:
                timeout = deadline - _time()
                if timeout < 0:
                    self._proc.terminate()
                    if check:
                        raise TimeoutError(self._flush_cache())
                    break
                time.sleep(0.02)
        return self._flush_cache()

    def _sync(self):
        n = 0
        if self._returncode is None:
            self._returncode = self._proc.poll()
            data = self._proc.stdout.read()
            n = len(data)
            if n:
                print('*', data)
                if self._startup_duration is None:
                    self._startup_duration = _time() - self._start_time
                self._put(data)
        return n

    @property
    def running(self):
        return self._returncode is None

class SSH(_Shell):

    def __init__(self, hostname=None, port=22, username=None, password=None):
        super(SSH, self).__init__()
        self._hostname = hostname or '127.0.0.1'
        self._port = port
        self._username = username
        self._password = password
        self._cache = b''
        self._closed = False
        self._client = None
        self._channel = None
        self._command_executing = False
        self._prompt =b'[sandbox@epm]##'
        self._ending = False
        self._cut_ending = True
        self._localhost = None
        self._origin_env_vars = {}
        self._cur = None

    def open(self, timeout=None):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self._hostname, port=self._port,
                       username=self._username, password=self._password)

        self._client = client
        self._channel = client.invoke_shell(term='')
        self._command_executing = True
        cmd = b'export PS1=' + self._prompt
        self.exec(cmd)
        self._cut_ending = False
        self.read_until(cmd, timeout=timeout, check=True)
        self._cut_ending = True
        self.call('set')
        env_vars = self.call('env', 10, check=True)

        for i in env_vars.split(b'\n'):
            item = i.split(b'=', 1)
            if len(item) == 2:
                key = item[0].decode('ascii')
                self._origin_env_vars[key] = item[1]

    def close(self):
        if self._client:
            self._client.close()

    def make_env(self, env):
        set = {}
        unset = []
        for k, v in env.items():
            if v is None:
                unset.append(v)
            else:
                set[k] = v

    @property
    def localhost(self):
        if self._localhost is None:
            self._localhost = self._client.get_transport().sock.getsockname()[0]
        return self._localhost

    def _sync(self):
        n = 0
        if self._channel.recv_ready():
            data = self._channel.recv(4096)
            n = len(data)
            if n == 0:
                self._closed = True
                self._command_executing = False
            else:
                self._ending = data.endswith(self._prompt)
                if self._ending:
                    if self._cut_ending:
                        data = data[: -1*len(self._prompt)]
                        n = len(data)
                self._put(data)
        return n

    def _flush(self):
        return self._get()

    def _write(self, data):
        n = self._channel.send(data)
        if n == 0:
            self._closed = True

    def _exports_cmd(self, env):
        if not env:
            return b''
        exports = b''
        for k, v in env.items():
            k = bytes(k, encoding=self.encoding)
            if v is None:
                exports += b'unset ' + k + b'; '
            else:
                v = bytes(v, encoding=self.encoding)
                exports += b'export ' + k + b'=' + v + b'; '
        return exports

    def exec(self, cmd, env=None):
        self._ending = False
        self._returncode = None
        if isinstance(cmd, list):
            cmd = " ".join(cmd)
        if not isinstance(cmd, str):
            cmd = str(cmd, encoding=self.encoding)
        cmd = cmd.strip() + '\n'
        cmd = bytes(cmd, encoding=self.encoding)
        cmd = self._exports_cmd(env) + cmd
        self._write(cmd)

    def call(self, cmd, timeout=None, env=None, check=False):
        self.exec(cmd, env)
        text = self.read(-1, timeout)
        if check and self.returncode:
            raise subprocess.SubprocessError(self.returncode, text)
        return text

    @property
    def running(self):
        return not self._closed and not self._ending

    @property
    def returncode(self):
        if self._returncode is None:
            self.exec(b'echo $?')
            i, m, txt = self.expect([b'(?P<code>\d+)'], 5)
            if m:
                self._returncode = int(m.group('code'))
            else:
                self._returncode = -1
        return self._returncode


class Runner(object):

    def __init__(self, profile, scheme, runner, api=None):
        self.config = get_runner_config(profile, scheme, runner, api)
        self._shell = None
        self._profile = profile
        self._scheme = scheme
        self._runner = runner



    @property
    def is_docker(self):
        return 'docker' in self.config

    @property
    def is_shell(self):
        return self.config['.type'] == 'shell'

    @property
    def is_ssh(self):
        return 'ssh' in self.config

    @property
    def shell(self):
        if self._shell is None:

            conf = self.config
            if conf['.type'] in ['shell', 'docker']:
                self._shell = Shell()
            elif 'ssh' in conf:
                hostname = conf['hostname']
                port = conf['ssh'].get('port', 22)
                username = conf['ssh'].get('username')
                password = conf['ssh'].get('password')
                self._shell = SSH(hostname=hostname, port=port, username=username, password=password)
            self._shell.open()
        return self._shell

    def exec(self, cmd, env=None):
        self.shell.exec(cmd, env=env)
        return self.shell

    def call(self, cmd, env=None, timeout=None, check=False):
        return self.shell.call(cmd, env, timeout, check)


class Sandbox(object):

    def __init__(self, profile=None, scheme=None, runner=None, api=None):
        self._api = api or API()
        self._project = Project(profile, scheme, self._api)
        self._runner = runner
        self._profile = profile
        self._scheme = scheme
        self._executor = Runner(profile, scheme, runner, api)

    def run(self, name, argv=[], env=None):
        env_vars = None
        config = self._executor.config
        program = os.path.join(self._project.folder.out, 'sandbox', name)
        program = os.path.normpath(program)

        if self._executor.is_ssh:
            return self._ssh(name, argv, env)
        elif self._executor.is_docker:
            docker = config['docker']
            env_vars = env_vars or {}
            env_vars['EPM_SANDBOX_IMAGE'] = docker['image']
            env_vars['EPM_SANDBOX_HOME'] = docker['home']
            env_vars['EPM_SANDBOX_SHELL'] = docker['shell']
            env_vars['EPM_SANDBOX_RUNNER'] = 'docker'

        else:
            pass

        if PLATFORM == 'Windows':
            program += '.cmd'
        command = '{} {}'.format(program, " ".join(argv))

        return self._executor.exec(command, env=env_vars)

    def _ssh(self, name, argv, env):
        config = self._executor.config
        username = config['localhost']['username']
        password = config['localhost']['password']

        program = pathlib.PurePath(os.path.join(self._project.folder.out, 'sandbox', name)).as_posix()
        sh = self._executor.shell
        conan_storage = self._api.conan_storage_path

        home = config['home']
        project = '{}/{}'.format(home, PROJECT_FOLDER)
        storage = '{}/{}'.format(home, CONAN_STORAGE)
        sandbox = '{}/{}'.format(home, SANDBOX_FOLDER)
        home = '{}/{}'.format(home, HOST_FOLDER)

        sh.call('mkdir -p {0}'.format(home), check=True)
        sh.call('[ -d {0} ] && rm -rf {0}'.format(sandbox))
        self._mount(os.path.abspath(self._project.dir), project, sh, username, password)
        self._mount(conan_storage, storage, sh, username, password)

        command = "cd {} && ".format(project)
        command += './' + pathlib.PurePath(program).as_posix()
        command = command + " ".join(argv)

        env = {'EPM_SANDBOX_HOME': home,
               'EPM_SANDBOX_STORAGE': storage,
               'EPM_SANDBOX_PROJECT': project
               }
        return self._executor.exec(command, env)

    def _mount(self, source, directory, sh, username, password):
        source = pathlib.PurePath(source).as_posix()
        directory = pathlib.PurePath(directory).as_posix()

        sh.call('[[ -d {0} ]] && umount {0}'.format(directory))

        formatter = 'mount -t nfs -o nolock {hostname}:{source} {directory}'

        if PLATFORM == 'Windows':
            source = source.replace(':', '')
            formatter = 'mount -t cifs -o user={username},pass={password},noserverino //{hostname}/{source} {directory}'

        # create folder, if not exits
        sh.call('[ ! -d {0} ] && mkdir {0}'.format(directory))
        localhost = sh.localhost

        cmd = formatter.format(hostname=localhost,
                               username=username,
                               password=password,
                               source=source,
                               directory=directory)
        sh.call(cmd, check=True)

