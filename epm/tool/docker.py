


class Docker(object):

    def __init__(self):
        self.volume = {}  # target: {source: str, readonly: false, type: 'bind'
        self.environment = {}  # environment name : value
