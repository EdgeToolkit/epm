from epm.model.project import Project

from collections import namedtuple
import os
import tempfile
import re
from conans.tools import rmdir, mkdir
from threading import Lock
import telnetlib

_DEFAULT_BLOCKSIZE = 8*1024


class Slice(object):
    DEFAULT_SIZE = 8 * 1024

    def __init__(self, cap=None):
        self._cap = cap or self.DEFAULT_SIZE
        self._buf = bytes()
        self._cur = 0
        self._end = 0

    def append(self, data):
        size = len(data)
        if self._end == self._cap:
            return data

        if size + self._end > self._cap:
            n = self._cap - self._end
            self._buf[self._end:] = data[:n]
            self._end += n
            return self._buf[n:]
        else:
            self._buf[self._end: self._end+size] = data
            self._end += size
            return []

    @property
    def size(self):
        return len(self._buf)

    def seek(self, offset, whence=0):
        if whence == 2:
            n = self.size - offset
            self._cur = n if n > 0 else 0
        elif whence == 1:
            remain = self.size - self._cur
            if remain > offset:
                self._cur += offset
            else:
                self._cur = self.size
        else:
            size = self.size
            self._cur = offset if offset < size else size

    def read(self, n):
        buf = self.check(n)
        self._cur += len(buf)
        return buf

    def check(self, n):
        """ try to read n bytes from current position,
        offset no changed

        :param n:
        :return:
        """
        remain = self.size - self._cur
        if remain <= 0:
            return bytes()

        if n < 0 or n >= remain:
            return self._buf[self._cur:]

        end = self._cur + n
        return self._buf[self._cur: end]




import re

class Scanner(object):

    def __init__(self, stream, offset=0):
        self._stream = stream
        self._begin = offset
        self._end = offset
        self._buf = bytes()

    def find(self, matche):
        return i, pos, text

    def expect(self, pattern):

        return i, pos, text

    def cursor(self):
        return self._begin

    def move(self, size):
        self._begin += size
        self._end = self._begin


class Stream(object):
    DEFAULT_SIZE = 8*1024

    def __init__(self, file=None):
        self._buf = bytes()
        self._file = None
        self._flushed = 0

    @property
    def size(self):
        return self._flushed + len(self._buf)

    def seek(self, offset):
        """

        :param offset: None means to current end of the stream
                       negative value means move from the end of
        :return:
        """
        return offset

    def read(self, size=-1):
        pass

    def peek(self, size=-1):
        pass

    def append(self, data):
        pass





class Block(object):

    def __init__(self, cache, index, capacity=_DEFAULT_BLOCKSIZE):
        self._cache = cache
        self._capacity = capacity
        self._buffer = None
        self._index = index
        self.heat = 0

    @property
    def index(self):
        return self._index

    @property
    def data(self):
        if self._buffer is None:
            with open(self.filename, "rb") as f:
                self._buffer = f.read()
        return self._buffer

    @property
    def filename(self):
        path = os.path.join(self._cache.dir, "{:0>5d}.log".format(self._index))
        return path


class LiveBlock(Block):

    def __init__(self, cache, index, capacity=_DEFAULT_BLOCKSIZE):
        super(LiveBlock, self).__init__(cache, index, capacity)
        self._lock = Lock()
        self._buffer = bytes()

    @property
    def data(self):
        with self._lock:
            return self._buffer

    def put(self, data):
        with self._lock:
            return self._put(data)

    def _put(self, data):
        size = len(data)
        bsize = len(self._buffer) if self._buffer else 0
        remain = self._capacity - bsize
        if remain > size:
            if self._buffer:
                self._buffer += data
            else:
                self._buffer = data
            return None
        else:
            self._buffer += data[:remain]
            with open(self.filename, "wb") as f:
                f.write(self._buffer)
            return data[remain:]

    def flush(self):
        with open(self.filename, "wb") as f:
            f.write(self._buffer)


class Cache(object):
    BLOCK_SIZE = _DEFAULT_BLOCKSIZE
    CACHE_POOL_SIZE = 8

    def __init__(self, path=None):
        if path:
            dir = os.path.abspath(path)
            rmdir(dir)
            mkdir(dir)
        self._dir = dir
        self._flushed = 0
        self._block = None
        self._lock = Lock()
        self._caches = {}

    @property
    def dir(self):
        if self._dir is None:
            self._dir = tempfile.mkdtemp(prefix="cache.")

        return self._dir

    @property
    def size(self):
        n = self._flushed * self.BLOCK_SIZE
        return n + len(self._buffer)

    def _update(self, block):

        if len(self._caches) > self.CACHE_POOL_SIZE:
            heat = None
            index = None
            for i, item in self._caches.items():
                if heat is None or heat > item.heat:
                    heat = item.heat
                    index = i
                block.heat = max(item.heat, block.heat)
            del self._caches[index]
        block.heat += 1
        self._caches[block.index] = block

    def _get_block(self, i):
        if i > self._flushed:
            raise IndexError(f"Cache block index out of range {i} > {self._flushed}")

        if i == self._flushed:
            if self._block is None:
                self._block = LiveBlock(self, self._flushed)
            return self._block
        if i in self._caches:
            block = self._caches[i]
            block.heat += 1
        else:
            block = Block(self, i)
            self._update(block)
        return block

    def put(self, data):
        while data:
            self._block = self._block or LiveBlock(self, self._flushed)
            data = self._block.put(data)
            if data:
                self._flushed += 1
                self._update(self._block)
                self._block = None

    def flush(self):
        if self._block and isinstance(self._block, LiveBlock):
            self._block.flush()

    @property
    def flushed(self):
        return self._flushed

    def read(self, pos, n):
        index, offset = self._locate(pos)
        block = self._get_block(index)
        if (offset + n) < len(block.data):
            return block.data[offset : offset+n ]

        buf = block.data[offset:]
        for i in range(index+1, self.flushed):
            block = self._get_block(index)
            if len(buf) + len(block.data) >= n:
                return buf + block.data[:n - len(buf)]
            buf += block.data
        return buf

    def _locate(self, pos):
        return int(pos / self.BLOCK_SIZE), pos % self.BLOCK_SIZE

    def find(self, obj, start):
        index, offset = self._locate(start)
        size = len(obj)

        block = self._get_block(index)
        buf = block.data[offset:]
        n = 0
        pos = 0
        while True:
            if len(buf) < size:
                if index < self.flushed:
                    block = self._get_block(index)
                    buf += block.data
                else:
                    return -1, start + pos
            else:
                pos = buf.find(obj)
                if pos == -1:
                    n += len(buf) - size
                    buf = buf[:size]
                else:
                    return start + pos, start + pos

    def expect(self, pattern, start, sep=b'\n'):
        index, offset = self._locate(start)
        block = self._get_block(index)
        buf = block.data[offset:]
        n = 0

        while True:
            pos = buf.find(sep, n)
            if pos == -1:
                if index >= self.flushed:
                    # try the not complete one
                    line = buf[n:]
                    m = re.match(pattern, line)
                    return m, n
                index += 1
                block = self._get_block(index)
                buf = buf[n:] + block.data
            else:
                line = buf[n:pos]
                m = re.match(pattern, line)
                if m:
                    return m, n
                n = pos


class Sandbox(object):

    def __init__(self, name, project):
        """

        :param project:
        :param name: program.executable name
        """
        pass

    @staticmethod
    def load(name, profile, scheme=None):
        project = Project(profile, scheme)
        return Sandbox(name, project)