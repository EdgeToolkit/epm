import subprocess
import threading
import time
import os
import psutil
from epm.utils.cache import Cache
from conans.tools import environment_append


class _Analyzer(object):

    def __init__(self, cache):
        self._cache = cache
        self._scanned = 0

    def find(self, obj, wait=None):
        begin = time.time()
        escape = 0
        while True:
            pos, self._scanned = self._cache.find(obj, self._scanned)
            if wait is None or escape > wait:
                return pos
            time.sleep(0.1)
            escape = time.time() - begin

    def expect(self, pattern, wait=None):
        begin = time.time()
        escape = 0
        while True:
            m, self._scanned = self._cache.expect(pattern, self._scanned)
            if wait is None or escape > wait:
                return m, self._scanned
            time.sleep(0.1)
            escape = time.time() - begin

    def read(self, pos, n):
        return self._cache.read(pos, n)

    @property
    def cache(self):
        return self._cache


class Process(object):
    STDOUT = 0
    STDERR = 1

    def __init__(self, command, argv=[], shell=False, cache_dir=None):
        self._command = command
        self._shell = shell
        self._proc = None
        self._argv = argv
        self._threads = [None, None]
        self._analyzer = [None, None]
        self._returncode = None
        self._cache_dir = cache_dir
        self._lock = threading.Lock()

    def start(self, argv=[], cwd=None, env=None):
        command = self._command + argv
        env_vars = env or {}
        with environment_append(env_vars):
            print('================== PATH ==========================')
            print(os.getenv('PATH'))
            print(os.getenv('EPM_SANDBOX_ARCHIVE'))
            print('============================================')
            self._proc = subprocess.Popen(command,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          cwd=cwd, shell=self._shell)

        for i in [Process.STDOUT, Process.STDERR]:
            pipe = self._proc.stdout if i == Process.STDOUT else self._proc.stderr
            cached = None
            if self._cache_dir:
                cached = "{}/{}".format(self._cache_dir, "stdout" if i == Process.STDOUT else "stderr")
            cache = Cache(path=cached)
            thread = threading.Thread(target=Process._capture, args=(self._proc, pipe, cache))

            self._analyzer[i] = _Analyzer(cache)
            self._threads[i] = thread

            thread.start()

    @property
    def stdout(self):
        return self._analyzer[Process.STDOUT]

    @property
    def stderr(self):
        return self._analyzer[Process.STDERR]

    @property
    def returncode(self):
        return self._proc.poll()

    def _term(self):
        for proc in psutil.process_iter():
            p = proc.parent()
            if p and p.pid == self._proc.pid:
                proc.terminate()

    def terminate(self):
        if self._shell:
            self._term()
        else:
            self._proc.terminate()

        for thread in self._threads:
            thread.join()

    @staticmethod
    def _capture(proc, pipe, cache):

        while proc.poll() is None:
            data = pipe.read1()
            if data:
                cache.put(data)
        cache.flush()
