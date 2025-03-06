class BasePlugin:
    def __init__(self, config):
        self._config = config

    def get_config(self):
        return self._config

    def get_context(self):
        raise NotImplementedError("get_context() needs to be implemented in sub-class")

    def get_template(self):
        raise NotImplementedError("get_template() needs to be implemented in sub-class.")
