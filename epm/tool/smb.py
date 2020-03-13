
from smb.SMBConnection import *
import pathlib
import fnmatch


class Client(object):

    def __init__(self, config):
        self._config = config

        self._hostname = config['hostname']
        self._username = config['username']
        self._password = config.get('password')

        self._service_name = config['driver']
        self._base_folder = config.get('base', '')
        self._smbc = None

    @property
    def smbc(self):
        if self._smbc is None:
            smb = SMBConnection(self._username, self._password, '', '', use_ntlm_v2=True)
            if not smb.connect(self._hostname):
                raise Exception('Failed connect to remote server')
            assert smb.auth_result
            self._smbc = smb
        return self._smbc

    def close(self):
        if self._smbc:
            self._smbc.close()

    def copyfile(self, src, dest):
        folder = os.path.dirname(dest or '.')
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        filename = dest
        path = os.path.join(self._base_folder, src)
        with open(filename, 'wb') as f:
            self.smbc.retrieveFile(self._service_name, path, f)
            f.close()

    def files(self, folder):
        ''' list the files with match the pattern in fnmatch

        :param patterns:
        :return:
        '''
        path = os.path.normpath(os.path.join(self._base_folder, folder))
        results = []
        for i in self.smbc.listPath(service_name=self._service_name, path=path):
            name = i.filename
            if name in ['.', '..']:
                continue

            if i.isDirectory:
                for j in self.files(os.path.join(folder, name)):
                    results.append('%s/%s' % (name, j))
            else:
                results.append(name)
        return results

    def copy(self, folder, patterns, dest):
        if isinstance(patterns, str):
            patterns = [patterns]
        files = self.files(folder)

        for pattern in patterns:
            n = 0
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    self.copyfile(os.path.join(folder, filename),
                                  os.path.join(dest, filename))
                    n +=1
            if n == 0:
                print('NO match file for pattern <%s> at %s.' % (pattern, folder))
