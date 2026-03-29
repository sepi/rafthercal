import functools


class BasePlugin:
    def __init__(self, config):
        self._config = config

    @classmethod
    def context_name(cls):
        """The key under which this plugin is exposed in the template context.
        Defaults to the class name with 'Plugin' stripped and lowercased.
        Override in subclasses when a different name is needed."""
        name = cls.__name__
        if name.endswith('Plugin'):
            name = name[:-6]
        return name.lower()

    @functools.cached_property
    def _context(self):
        return self.get_context()

    def __getattr__(self, name):
        # Prevent recursion for private attributes and avoid masking real
        # AttributeErrors during __init__ or cached_property setup.
        if name.startswith('_'):
            raise AttributeError(name)
        try:
            return self._context[name]
        except KeyError:
            raise AttributeError(
                f"{type(self).__name__!r} context has no key {name!r}"
            )

    def get_config(self):
        return self._config

    def get_context(self):
        raise NotImplementedError("get_context() needs to be implemented in sub-class")
