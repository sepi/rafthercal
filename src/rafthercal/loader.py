import importlib
import pathlib
import sys


def _class_name_from_stem(stem):
    """calendar_plugin -> CalendarPlugin"""
    return ''.join(part.title() for part in stem.split('_'))


def _load_from_dir(directory, package=None):
    """Yield (class_name, klass) for all *_plugin.py files in directory."""
    for path in sorted(pathlib.Path(directory).glob('*_plugin.py')):
        class_name = _class_name_from_stem(path.stem)
        if package:
            module = importlib.import_module(f'{package}.{path.stem}')
        else:
            if str(directory) not in sys.path:
                sys.path.insert(0, str(directory))
            module = importlib.import_module(path.stem)
        klass = getattr(module, class_name, None)
        if klass is not None:
            yield class_name, klass


def load_plugin_classes(config):
    plugin_classes = {}

    # Built-in plugins from the package directory
    builtin_dir = pathlib.Path(__file__).parent
    for name, klass in _load_from_dir(builtin_dir, package='rafthercal'):
        plugin_classes[name] = klass

    # Optional user-defined plugin directory
    extra_dir = getattr(config, 'RAFTHERCAL_PLUGIN_DIR', None)
    if extra_dir:
        for name, klass in _load_from_dir(extra_dir):
            plugin_classes[name] = klass

    return plugin_classes
