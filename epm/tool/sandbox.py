import os
import queue
import threading
import telnetlib
import paramiko
import time
import  subprocess
from abc import ABC, abstractmethod
from time import monotonic as _time

from epm.api import API
from epm.model.project import Project


def get_runner_config(profile, scheme, runner, api=None):
    import copy
    from epm.api import API
    if runner == 'shell':
        return {'.type': 'shell'}

    api = api or API()
    project = Project(profile, scheme, api)
    profile = project.profile

    if runner in [None, 'auto']:

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
        print('[+]', config)
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

    @abstractmethod
    def open(self, timeout=None):
        pass

    @abstractmethod
    def close(self):
        pass

    def read(self, n=-1, timeout=None):
        buf = self._get(n)
        if len(buf) == n:
            return buf

        if timeout is not None:
            deadline = _time() + timeout

        while self.running:
            self._sync()
            buf += self._get(n)
            if n == len(buf):
                return buf

            if timeout is not None:
                timeout = deadline - _time()
                if timeout < 0:
                    break
            time.sleep(0.02)
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
            time.sleep(0.02)

        if check:
            raise TimeoutError(self._get())
        return self._get()

    def expect(self, list, timeout=None):
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
        while not self.eof:
            self._sync_cache()
            for i in indices:
                m = list[i].search(self._cache)
                if m:
                    e = m.end()
                    text = self._cache[:e]
                    self._cache = self._cache[e:]
                    return (i, m, text)
            if timeout is not None:
                timeout = deadline - _time()
                if timeout < 0:
                    break
                time.sleep(0.02)

        text = self._flush_cache()
        if not text and self.eof:
            raise EOFError
        return (-1, None, text)

    @abstractmethod
    def exec(self, cmd, env=None):
        pass

    def read(self, nbytes=4096):
        raise NotImplemented('read not implemented.')

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
        self._returncode = None
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)



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
        if self._returncode is None:
            self._returncode = self._proc.poll() #subprocess.Popen.poll(self._proc)
            data = self._proc.stdout.read()
            self._put(data)
            return len(data)
        return 0

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
        self._exit_code = None

    def open(self, timeout=None):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self._hostname, port=self._port,
                       username=self._username, password=self._password)

        self._client = client
        self._channel = client.invoke_shell(term='')

        self.write('export PS1=\n')
        self.read_until('export PS1=', timeout=timeout, check=True)

    def _sync(self):
        if self._channel.recv_ready():
            data = self._channel.recv(4096)
            if len(data) == 0:
                self._closed = True
                return
            self._put(data)

    def _write(self, data):
        n = self._channel.send(data)
        if n == 0:
            self._closed = True

    def exec(self, cmd, env=None):
        self._exit_code = None
        if isinstance(cmd, list):
            cmd = " ".join(cmd)
        if not isinstance(cmd, str):
            cmd = str(cmd, encoding=self.encoding)
        cmd = cmd.strip() + '\n'
        cmd = bytes(cmd, encoding=self.encoding)
        if env:
            assert env, 'not support'
        self._write(cmd)

    def call(self, cmd, timeout=None, env=None, check=False):
        self.exec(cmd + ';echo [_<_<__exit__.code=$?>_>_]')
        i, m, txt = self.expect([r'\[\<_\<__exit__.code=(?<code>\d+)\>\_\>\]'], timeout)
        if check:
            code = int(m.group('code'))
            if code:
                raise subprocess.SubprocessError(code, txt)
        return txt

    @property
    def eof(self):
        return self._closed

    @property
    def exit_code(self):
        if self._exit_code is None:
            self._write(b'echo $?')

            i, m, txt = self.expect([b'(?P<code>\d+)'], 5)
            if m:
                self._exit_code = int(m.group('code'))
            else:
                self._exit_code = -1
        return self._exit_code


class Runner(object):

    def __init__(self, profile, scheme, runner, api=None):
        self.config = get_runner_config(profile, scheme, runner, api)
        self._shell = None

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
                hostname = conf['ssh'].get('hostname')
                port = conf['ssh'].get('port', 22)
                username = conf['ssh'].get('username')
                password = conf['ssh'].get('password')
                self._shell = SSH(hostname=hostname, port=port, username=username, password=password)
            self._shell.open()
        return self._shell

    def exec(self, cmd):
        self.shell.exec(cmd)
        return self.shell


class Sandbox(object):

    def __init__(self, profile=None, scheme=None, runner=None, api=None):
        self._api = api or API()
        self._runner = runner
        self._profile = profile
        self._scheme = scheme
        self._executor = Runner(profile, scheme, runner, api)

    def run(self, name, argv=[], env=None):
        program = os.path.normpath(os.path.join(self._api.project.folder.out, 'sandbox', name))
        env_vars = {}
        config = self._executor.config
        if self._executor.is_docker:
            docker = config['docker']
            env_vars['EPM_SANDBOX_IMAGE'] = docker['image']
            env_vars['EPM_SANDBOX_HOME'] = docker['home']
            env_vars['EPM_SANDBOX_SHELL'] = docker['shell']
            env_vars['EPM_SANDBOX_RUNNER'] = 'shell'
        elif self._executor.is_ssh:
            pass
            # mount

        #command = "{} {}".format(program, " ".join(argv))

        return self._executor.exec(command)

    def _mount(self):
        from epm.model.sandbox import HOST_FOLDER, PROJECT_FOLDER, CONAN_STORAGE, SANDBOX_FOLDER
        config = self._executor.config
        conan_storage = self._api.conan_storage_path
        env = {'CONAN_STORAGE_PATH': conan_storage}
        localhost = config['localhost']
        home = config['home']
        project = '{}/{}'.format(home, PROJECT_FOLDER)
        storage = '{}/{}'.format(home, CONAN_STORAGE)
        sandbox = '{}/{}'.format(home, SANDBOX_FOLDER)
        home = '{}/{}'.format(home, HOST_FOLDER)
        ssh = self._executor.shell

        cmd = 'mkdir -p {0}'.format(home)
        ssh.call(cmd, check=True)

        cmd = '[ -d {0} ] && rm -rf {0}'.format(sandbox)
        ssh.call(cmd)

        def _mnt(path, directory):
            cmd = '[ ! -d {0} ] && mkdir {0}'.format(directory)
            ssh.call(cmd)

            ssh.mount(path, directory,
                      interface=localhost['hostname'],
                      username=localhost['username'],
                      password=localhost['password'])

        WD = os.path.abspath('.')

        _mnt(WD, project)
        _mnt(conan_storage, storage)

        command = "export EPM_SANDBOX_HOME={};".format(home)
        command += "export EPM_SANDBOX_STORAGE={};".format(storage)
        command += "export EPM_SANDBOX_PROJECT={};".format(project)
        command += "cd {} && ".format(project)
        command += './' + pathlib.PurePath(filename).as_posix()
        command = [command] + argv
        # print('--->', command)
        return ssh.call(command)






class QueueOutput(object):
    """ wraps an output stream, so it can be pretty colored,
    and auxiliary info, success, warn methods for convenience.
    """

    def __init__(self, queue):
        self.queue = queue

    @property
    def is_terminal(self):
        return False

    def writeln(self, data, front=None, back=None, error=False):
        self.write(data, front, back, newline=True, error=error)

    def write(self, data, front=None, back=None, newline=False, error=False):
        self.queue.put(data)

    def info(self, data):
        self.writeln(data)

    def highlight(self, data):
        self.writeln(data)

    def success(self, data):
        self.writeln(data)

    def warn(self, data):
        self.writeln("WARN: {}".format(data))

    def error(self, data):
        self.writeln("ERROR: {}".format(data))

    def input_text(self, data):
        self.write(data)

    def rewrite_line(self, line):
        tmp_color = self._color
        self._color = False
        TOTAL_SIZE = 70
        LIMIT_SIZE = 32  # Hard coded instead of TOTAL_SIZE/2-3 that fails in Py3 float division
        if len(line) > TOTAL_SIZE:
            line = line[0:LIMIT_SIZE] + " ... " + line[-LIMIT_SIZE:]
        self.write("\r%s%s" % (line, " " * (TOTAL_SIZE - len(line))))

    def flush(self):
        pass


class _Sandbox(object):

    def __init__(self, name, profile=None, scheme=None, runner=None, directory=None):
        self._directory = os.path.abspath(directory or '.')
        self._name = name
        self._runner = runner
        self._profile = profile
        self._scheme = scheme
        self._queue = queue.Queue()
        self._out = QueueOutput(self._queue)
        self._api = API(output=self._out)
        self._running = None
        self._worker = None
        self._encoding = 'utf-8'
        self._cache = b''
        self._hostname = '127.0.0.1'
        self._localhost = '127.0.0.1'


    def startup(self, argv=[]):
        """ startup sandbox program `name`
        :param argv:
        :return:
        """

        # startup via api in another thread
        param = {'command': self._name,
                 'args': argv,
                 'PROFILE': self._profile,
                 'SCHEME': self._scheme,
                 'RUNNER': self._runner
                 }

        def worker(api, args):
            api.sandbox(args)

        self._worker = threading.Thread(target=worker, args=(self._api, param))
        self._worker.setDaemon(True)
        self._worker.start()
        return self._worker

    def read_all(self):
        """Read all data until program exits."""
        result = b''
        while not self.eof:
            value = self._read_once()
            if value:
                result += value
            else:
                time.sleep(0.1)
        return result

    def _read_once(self):
        print('{}'.format('.' if self._queue.empty() else '*'))
        if not self._queue.empty():
            value = self._queue.get()
            print('*', value, type(value))
            return value if isinstance(value, bytes) else value.encode(self._encoding)
        return b''

    @property
    def eof(self):
        return self._queue.empty() and not self._worker.is_alive()
    

    def _sync(self, timeout=None):
        print('sync:', timeout)
        while not self.eof:
            buf = self._read_once()
            if buf:
                self._cache += buf
                continue

            if timeout is not None:                
                deadline = _time() + timeout
                timeout = deadline - _time()
                if timeout < 0:
                    break
            time.sleep(0.1)

    def join(self, timeout=None):
        self._worker.join(timeout)

    def read_until(self, match, timeout=None):
        """Read until a given string is encountered or until timeout.

        When no match is found, return whatever is available instead,
        possibly the empty string.  Raise EOFError if the connection
        is closed and no cooked data is available.

        """
        if isinstance(match, str):
            match = match.encode(self._encoding)
        n = len(match)
        while self.eof:
            print('[X]')
            self._sync(0)
            i = self._cache.find(match)
            if i >= 0:
                i = i+n
                buf = self._cache[:i]
                self._cache = self._cache[i:]
                return buf

            if timeout is not None:
                deadline = _time() + timeout
                timeout = deadline - _time()
                if timeout < 0:
                    break
                time.sleep(0.5)
        return self.read_very_lazy()

    def expect(self, list, timeout=None):
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
                list[i] = re.compile(list[i])
        if timeout is not None:
            deadline = _time() + timeout

        while self._worker.is_alive():
            self._sync_cache()
            for i in indices:
                m = list[i].search(self._cache)
                if m:
                    e = m.end()
                    text = self._cache[:e]
                    self._cache = self._cache[e:]
                    return (i, m, text)

            if timeout is not None:
                timeout = deadline - _time()
                if timeout < 0:
                    break
            time.sleep(0.1)

        text = self.read_very_lazy()
        if not text and self.eof:
            raise EOFError

        return (-1, None, text)

    def read_very_lazy(self):
        """Return any data available in the cooked queue (very lazy).

        Raise EOFError if thread exist and no data available.
        Return b'' if no cooked data available otherwise.  Don't block.

        """
        buf = self._cache
        self._cache = b''
        if not buf and self._cache:
            raise EOFError('{} already exists.'.format(self._name))
        return buf
