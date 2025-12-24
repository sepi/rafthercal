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
        'line_single': "─" * 32,
        'line_double': "═" * 32,
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


def main():
    context = load_context()
    template = load_main_template()

    rml_str = template.render(context)
    PRINT_RML_ONLY = getattr(config, 'RAFTHERCAL_PRINT_RML_ONLY', False)
    if PRINT_RML_ONLY:
        print(rml_str)
    else:
        out_file = config.RAFTHERCAL_SERIAL_DEVICE or sys.stdout
        if config.RAFTHERCAL_SIMULATE_PRINTER:
            import io
            out_file = io.BytesIO()
    
        print_from_str(rml_str, out_file)
    
        if config.RAFTHERCAL_SIMULATE_PRINTER:
            simulate_print(out_file)


def button_loop():
    if type(config.RAFTHERCAL_BUTTON_PIN) == int: # Read from GPIO
        from gpiozero import Button
        button = Button(config.RAFTHERCAL_BUTTON_PIN)
        wait_message = f"Waiting for button press connected to pin {config.RAFTHERCAL_BUTTON_PIN}"
        wait_fn = lambda: button.wait_for_press()
    else: # Read from keyboard
        wait_message = f"Waiting <ENTER> button press on keyboard."
        wait_fn = lambda: type(input()) == str

    print(wait_message)
    while wait_fn():
        try:
            print("Fetching data then printing...")
            main()
            print(wait_message)
        except Exception as e:
            print("A problem occured, ignoring: ", e)


if __name__ == '__main__':
    main()
