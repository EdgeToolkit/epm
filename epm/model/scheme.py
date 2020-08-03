from conans.model.options import OptionsValues
from epm.util import system_info

PLATFORM, ARCH = system_info()


class Scheme(object):

    def __init__(self, project, name=None):
        self._name = name or project.attribute.scheme
        self._project = project

    @property
    def name(self):
        return self._name

    def _get_options(self, package):
        api = self.project.api
        settings = self.project.profile.settings
        metainfo = self.project.metainfo
        options, package_options = metainfo.get_options(self.name, settings, storage=None, api=api)

        items = dict()
        for key, value in options.items():
            if package:
                key = '%s:%s' % (self.project.name, key)
            items[key] = value

        for name, opts in package_options.items():
            for k, v in opts.items():
                key = '%s:%s' % (name, k)
                items[key] = v
        return items

    def _options(self, package=False):
        return OptionsValues(self._get_options(package))

    @property
    def options(self):
        return self._options(False)

    @property
    def package_options(self):
        return self._options(True)



























class _Scheme(object):

    def __init__(self, name, project):
        self._name = name
        self._scheme = None  # options name
        self._api = None
        self.project = project

    @property
    def name(self):
        return self._name

    def _get_options(self, package):
        api = self.project.api
        settings = self.project.profile.settings
        metainfo = self.project.metainfo
        options, package_options = metainfo.get_options(self.name, settings, storage=None, api=api)

        items = dict()
        for key, value in options.items():
            if package:
                key = '%s:%s' % (self.project.name, key)
            items[key] = value

        for name, opts in package_options.items():
            for k, v in opts.items():
                key = '%s:%s' % (name, k)
                items[key] = v
        return items

    def _options(self, package=False):
        return OptionsValues(self._get_options(package))

    @property
    def options(self):
        return self._options(False)

    @property
    def package_options(self):
        return self._options(True)

