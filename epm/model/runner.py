

class Runner(object):

    def __init__(self, name=None):
        """
        :param name: the name of runner in config.yml
        """
        self._name = name
        self.volume = {}  # {dst: { 'bind': from, 'mode': 'ro|rw' }
        self.environment = {}
        pass

