class Worker(object):

    def __init__(self, api=None):
        self._api = api
        self._out = None

    @property
    def api(self):
        if self._api is None:
            from epm.api import API
            self._api = API()
        return self._api

    @property
    def out(self):
        if self._out is None:
            self._out = self._api.out
        return self._out

    @property
    def conan(self):
        return self.api.conan

