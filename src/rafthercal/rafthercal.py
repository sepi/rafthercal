import sys
from  datetime import date, datetime, timedelta
import time

from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape
from rml.rml import print_from_str
from rml.simulate import simulate_print

from rafthercal.loader import load_plugin_classes
from rafthercal.config_helpers import config_template_from_pattern
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


def load_template(filename):
    jinja_env = Environment(
        loader=ChoiceLoader([FileSystemLoader("templates"),
                             PackageLoader("rafthercal", "templates")
                             ]),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = jinja_env.get_template(filename)
    return template


def main(template="main.rml"):
    print(f"Printing template '{template}.'")

    PRINT_RML_ONLY = getattr(config, 'RAFTHERCAL_PRINT_RML_ONLY', False)
    SIMULATE_PRINTER = getattr(config, 'RAFTHERCAL_SIMULATE_PRINTER', False)

    out_file = config.RAFTHERCAL_SERIAL_DEVICE or sys.stdout

    if not PRINT_RML_ONLY and not SIMULATE_PRINTER:
        print_from_str("{feedL 1}", out_file)

    context = load_context()
    template = load_template(template)

    rml_str = template.render(context)
    if PRINT_RML_ONLY:
        print(rml_str)
    else:
        if SIMULATE_PRINTER:
            import io
            out_file = io.BytesIO()
    
        print_from_str(rml_str, out_file)
    
        if SIMULATE_PRINTER:
            simulate_print(out_file)


def analyze_sequence(sequence, threshold):
    "Analyze a sequence of up and down timestamps and return as a list of '.' and '-'."
    # Convert button down and up timestamps to relative to first button down event times (in seconds).
    seq_rel = [(s - sequence[0]).total_seconds() for s in sequence]

    # Button press durations
    durations = [down-up for up, down in zip(seq_rel[::2], seq_rel[1::2])]

    pattern = ['.' if d < threshold else '-' for d in durations]
    return pattern
            

def button_loop():
    button_down = False
    in_sequence = False
    sequence_times = []

    def on_press():
        nonlocal button_down, in_sequence, sequence_times
        if not button_down:
            if not in_sequence:
                in_sequence = True
            sequence_times.append(datetime.now())
            button_down = True

    def on_release():
        nonlocal button_down
        if button_down:
            if in_sequence:
                sequence_times.append(datetime.now())
            button_down = False


    if type(config.RAFTHERCAL_BUTTON_PIN) == int: # Read from GPIO
        from gpiozero import Button
        button = Button(config.RAFTHERCAL_BUTTON_PIN, bounce_time=0.05) # With software debounce of 50ms
        button.when_pressed = on_press
        button.when_released = on_release
        wait_message = f"Waiting for button press pattern connected to pin {config.RAFTHERCAL_BUTTON_PIN}"
    else: # Read from keyboard
        from pynput import keyboard
        wait_message = f"Waiting <ENTER> button press pattern on keyboard."

        def on_kb_press(key):
            if key == keyboard.Key.enter:
                on_press()

        def on_kb_release(key):
            if key == keyboard.Key.enter:
                on_release()

        listener = keyboard.Listener(
            on_press=on_kb_press,
            on_release=on_kb_release
        )
        listener.start()

    print(wait_message)
    while True:
        try:
            if datetime.now() > sequence_times[-1] + timedelta(seconds=0.55) and not button_down:
                pattern = analyze_sequence(sequence_times, 0.15)
                pattern_str = ''.join(pattern)
                template = config_template_from_pattern(config, pattern_str)
                if template:
                    print(f"Detected pattern '{pattern_str}'. Fetching data then printing...")
                    main(template)
                    print(wait_message)
                else:
                    print("No template found.")
                sequence_times = []
                in_sequence = False
        except IndexError:
            pass
        except Exception as e:
            print("A problem occured, ignoring: ", e)

        time.sleep(.2)


if __name__ == '__main__':
    main()
