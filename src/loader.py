import config

def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def load_plugin_classes():
    plugin_classes = {}
    for mod_class_name in config.RAFTHERCAL_PLUGIN_CLASSES:
        klass = my_import(mod_class_name)
        plugin_classes[mod_class_name] = klass
    return plugin_classes
