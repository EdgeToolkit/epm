#import paramiko
#import time
#from time import monotonic as _time
#import  subprocess
#
#
#
#class _Shell(object):
#
#    def __init__(self):
#
#        self.encoding = 'utf-8'
#        self._cache = b''
#        self._binary_mode = True
#        self._exit_code = None
#
#
#    def open(self, timeout=None):
#        raise NotImplementedError('open method not implemented.')
#
#    def close(self):
#        raise NotImplementedError('close method not implemented.')
#
#    def read_until(self, match, timeout=None, check=False):
#        """Read until a given string is encountered or until timeout.
#
#        When no match is found, return whatever is available instead,
#        possibly the empty string.  Raise EOFError if the connection
#        is closed and no cooked data is available.
#        if check set, raise TimeoutError when timeout
#
#        """
#        if self._binary_mode:
#            if isinstance(match, str):
#                match = bytes(match, encoding=self.encoding)
#        n = len(match)
#        i = self._cache.find(match)
#        if i >= 0:
#            i = i + n
#            buf = self._cache[:i]
#            self._cache = self._cache[i:]
#            return buf
#
#        if timeout is not None:
#            deadline = _time() + timeout
#
#        while not self.eof:
#            i = max(0, len(self._cache) - n)
#            self._sync_cache()
#
#            i = self._cache.find(match, i)
#
#            if i >= 0:
#                i = i + n
#                buf = self._cache[:i]
#                self._cache = self._cache[i:]
#                return buf
#
#            if timeout is not None:
#                timeout = deadline - _time()
#                if timeout < 0:
#                    if check:
#                        raise TimeoutError(self._flush_cache())
#                    break
#            time.sleep(0.02)
#
#        return self._flush_cache()
#
#    def _flush_cache(self):
#        """Return any data available in the cache. and clear it
#        """
#        buf = self._cache
#        self._cache = b''
#        return buf
#
#
#    def expect(self, list, timeout=None):
#        """Read until one from a list of a regular expressions matches.
#
#        The first argument is a list of regular expressions, either
#        compiled (re.RegexObject instances) or uncompiled (strings).
#        The optional second argument is a timeout, in seconds; default
#        is no timeout.
#
#        Return a tuple of three items: the index in the list of the
#        first regular expression that matches; the match object
#        returned; and the text read up till and including the match.
#
#        If EOF is read and no text was read, raise EOFError.
#        Otherwise, when nothing matches, return (-1, None, text) where
#        text is the text received so far (may be the empty string if a
#        timeout happened).
#
#        If a regular expression ends with a greedy match (e.g. '.*')
#        or if more than one expression can match the same input, the
#        results are undeterministic, and may depend on the I/O timing.
#
#        """
#        re = None
#        list = list[:]
#        indices = range(len(list))
#        for i in indices:
#            if not hasattr(list[i], "search"):
#                if not re: import re
#                pattern = list[i]
#                if isinstance(pattern, str):
#                    if self._binary_mode:
#                        pattern = bytes(pattern, encoding=self.encoding)
#                list[i] = re.compile(pattern)
#        if timeout is not None:
#            deadline = _time() + timeout
#        while not self.eof:
#            self._sync_cache()
#            for i in indices:
#                m = list[i].search(self._cache)
#                if m:
#                    e = m.end()
#                    text = self._cache[:e]
#                    self._cache = self._cache[e:]
#                    return (i, m, text)
#            if timeout is not None:
#                timeout = deadline - _time()
#                if timeout < 0:
#                    break
#                time.sleep(0.02)
#
#        text = self._flush_cache()
#        if not text and self.eof:
#            raise EOFError
#        return (-1, None, text)
#
#    def exec(self, cmd):
#        raise NotImplementedError('exec method not implemented.')
#
#    def read(self):
#        raise NotImplementedError('read method not implemented.')
#
#    def write(self):
#        raise NotImplementedError('write method not implemented.')
#
#    def _sync_cache(self, nbytes=None):
#        raise NotImplementedError('_sync_cache method not implemented.')
#
#    @property
#    def exit_code(self):
#        return self._exit_code
#
#
#class Shell(_Shell):
#
#    def __init__(self):
#        super(Shell, self).__init__()
#        self._proc = None
#
#    def open(self):
#        pass
#
#    def exec(self, cmd):
#        self._exit_code = None
#        print(cmd)
#        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
#
#    def _sync_cache(self, nbytes=4096):
#        self._exit_code = subprocess.Popen.poll(self._proc)
#        if self._exit_code is None:
#            data = self._proc.stdout.read()
#            self._cache += data
#
#    @property
#    def eof(self):
#        return self._exit_code is not None
#
#class SSH(_Shell):
#
#    def __init__(self, hostname=None, port=22, username=None, password=None):
#        super(SSH, self).__init__()
#        self._hostname = hostname or '127.0.0.1'
#        self._port = port
#        self._username = username
#        self._password = password
#        self._cache = b''
#        self._closed = False
#        self._client = None
#        self._channel = None
#        self._exit_code = None
#
#    def open(self, timeout=None):
#        client = paramiko.SSHClient()
#        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#        client.connect(hostname=self._hostname, port=self._port,
#                       username=self._username, password=self._password)
#
#        self._client = client
#        self._channel = client.invoke_shell(term='')
#
#        self.write(b'export PS1=\n')
#        self.read_until(b'export PS1=', timeout=10, check=True)
#
#    def _sync_cache(self, nbytes=4096):
#        if self._channel.recv_ready():
#            data = self._channel.recv(nbytes)
#            if len(data) == 0:
#                self._closed = True
#                return
#            self._cache += data
#
#    def write(self, data):
#
#        n = self._channel.send(data)
#        if n == 0:
#            self._closed = True
#
#    def read(self, timeout=None):
#        buf = b''
#        if timeout is not None:
#            deadline = _time() + timeout
#        while not self.eof:
#            if self._channel.recv_ready():
#                buf += self._channel.recv(4096)
#                print(buf)
#            else:
#                if timeout is not None:
#                    timeout = deadline - _time()
#                    if timeout < 0:
#                        break
#        return buf
#
#    def exec(self, cmd):
#        self._exit_code = None
#        if isinstance(cmd, list):
#            cmd = " ".join(cmd)
#        if not isinstance(cmd, str):
#            cmd = str(cmd, encoding=self.encoding)
#        cmd = cmd.strip() + '\n'
#        cmd = bytes(cmd, encoding=self.encoding)
#        self.write(cmd)
#
#    @property
#    def eof(self):
#        return self._closed
#
#    @property
#    def exit_code(self):
#        if self._exit_code is None:
#            self.write(b'echo $?')
#
#            i, m, txt = self.expect([b'(?P<exit_code>\d+)'], 5)
#            if m:
#                self._exit_code = int(m.group('exit_code'))
#            else:
#                self._exit_code = -1
#        return self._exit_code
#
#
#
#if __name__ == '__main__':
#
#    sh = SSH('172.16.192.242', 16666, 'admin', 'admin123')
#    #sh = Shell()
#    sh.open()
#    sh.exec('ls -l')
#    print(sh.expect(['tmp']))
#    print('---------------------------')
#    print(sh.exit_code, type(sh.exit_code))

