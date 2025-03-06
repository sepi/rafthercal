import sys
from  datetime import date, datetime

from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape
from rml.rml import print_from_str
from rml.simulate import simulate_print

from rafthercal.loader import load_plugin_classes
import config

def load_context():
    base_context = {
        'today': date.today(),
        'now': datetime.now().time(),
        'line_width': 32,
        'line': "-" * 32,
    }

    plugin_classes = load_plugin_classes()
    plugins = [klass(config) for _, klass in plugin_classes.items()]

    # Collect contexts from all plugins
    context = base_context
    for p in plugins:
        context.update(p.get_context())

    return context

def load_main_template():
    jinja_env = Environment(
        loader=ChoiceLoader([FileSystemLoader("templates"),
                             PackageLoader("rafthercal", "templates")
                             ]),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = jinja_env.get_template(config.RAFTHERCAL_MAIN_TEMPLATE)
    return template

def main(simulate=False):
    context = load_context()
    template = load_main_template()
    rml_str = template.render(context)
    out_file = config.RAFTHERCAL_SERIAL_DEVICE or sys.stdout
    if simulate:
        import io
        out_file = io.BytesIO()
    print_from_str(rml_str, out_file)
    if simulate:
        simulate_print(out_file)

if __name__ == '__main__':
    main()
