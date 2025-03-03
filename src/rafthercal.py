import sys
import os
import platform
from  datetime import date, datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape
from rml.rml import print_from_str

from loader import load_plugin_classes

import config

base_context = {
    'today': date.today(),
    'now': datetime.now().time(),
    'line': "----------------------------",
}

plugin_classes = load_plugin_classes()
plugins = [klass(config) for _, klass in plugin_classes.items()]

# Collect contexts from all plugins
context = base_context
for p in plugins:
    context.update(p.get_context())

jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)

try:
    template_name = sys.argv[1]
except IndexError:
    template_name = "main.rml"

template = jinja_env.get_template(template_name)


out_str = template.render(context)

print_from_str(out_str, sys.stdout)
