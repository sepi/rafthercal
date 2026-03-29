# rafthercal

Rafthercal stands for _Raf's thermal printer calendar_. It's a Python 3
application that can run on a machine connected to a thermal printer
like the ones used in cash registers. It is primarily meant to print
*calendars* and *todo lists* from CalDAV online calendars.

The formatting of the printed output is customizable via
[jinja2](https://jinja.palletsprojects.com/en/stable/templates/)
templates and formatting directives of the [Receipt Markup Language
(RML)](https://github.com/sepi/RML) are accepted to format and style
the output.

Data is provided to templates by plugins. Built-in plugins cover
calendars, todo lists, system info, owner info and images. You can add
your own without modifying the application.

By default, the application is triggered via a button. You can also tap
a pattern (like morse code) to select between different print templates.
A short press can for example print your todo list while a long press
prints the calendar.


## Hardware
The usual hardware to run this project on is a Raspberry Pi. It can
easily interface with a cheap RS232 thermal printer found on Chinese
e-commerce sites and a pushbutton wired to a GPIO pin.


## Installation

Clone the repository and run the install script:

```
$ git clone https://github.com/sepi/rafthercal.git
$ cd rafthercal
$ bash scripts/install-rafthercal
```

The script will:
1. Create a Python virtual environment in the project directory
2. Install all dependencies via `pip-sync`
3. Install and start both systemd user services (`rafthercal` and `rafthercal-web`)

Before the services will be useful you need to configure the application (see below).


## Update

Run `$ update-rafthercal` or use the **Update app** button in the web UI.


## Configuration

### Web UI

The easiest way to configure rafthercal is via the web interface, which
runs on port 5000:

```
http://<your-pi-hostname-or-ip>:5000
```

From there you can edit `config.py` and all templates directly in the browser.
Use the **Restart service** button to apply changes.

The web UI is configured entirely via environment variables, making it easy
to override with systemd drop-in files in `~/.config/systemd/user/rafthercal-web.service.d/`:

| Variable | Description | Default |
|---|---|---|
| `RAFTHERCAL_CONFIG_DIR` | Directory containing `config.py` and local `templates/` | current working directory |
| `WEB_USERNAME` | Basic auth username (auth disabled if unset) | — |
| `WEB_PASSWORD` | Basic auth password (auth disabled if unset) | — |

Example drop-in (`~/.config/systemd/user/rafthercal-web.service.d/local.conf`):

```ini
[Service]
Environment=RAFTHERCAL_CONFIG_DIR=/home/pi/rafthercal
Environment=WEB_USERNAME=admin
Environment=WEB_PASSWORD=secret
```

After editing: `systemctl --user daemon-reload && systemctl --user restart rafthercal-web`

The `--config-dir` command-line flag takes precedence over `RAFTHERCAL_CONFIG_DIR` if both are set.

### Manual configuration

Copy the sample config and edit it:

```
$ cp src/rafthercal/config.py.sample config.py
```

Important values to set:

* `RAFTHERCAL_SERIAL_DEVICE` — path to the printer device (e.g. `/dev/ttyS0`)
* `RAFTHERCAL_BUTTON_PIN` — GPIO pin for the button; set to `None` to use the Enter key instead
* `RAFTHERCAL_TEMPLATES` — maps button press patterns to template files
* `CALDAV_SERVERS` — URL, username and password of your CalDAV server(s)
* `CALDAV_CALENDARS` — calendars to include in the printout
* `CALDAV_TODOS` — todo lists to include in the printout

The sample file contains comments with full documentation for every option.


## Running rafthercal

If installed via the install script the service starts automatically. To
control it manually:

```
$ systemctl --user start|stop|restart|status rafthercal
```

Or run it directly (useful for testing):

```
$ python3 -m rafthercal
```

This enters a loop waiting for a button press pattern. Press Ctrl-C to exit.


## Templates

Built-in templates live in `src/rafthercal/templates/`. To customise
one, create a file with the same name in a `templates/` directory next
to your `config.py` — it will take precedence over the built-in version.
New templates go in the same `templates/` directory and can be referenced
from `RAFTHERCAL_TEMPLATES` in the config.

Templates use [Jinja2](https://jinja.palletsprojects.com/en/stable/templates/).

### Context variables

Each plugin exposes its data under its own name in the template context.
Access them with dot notation:

| Variable | Plugin | Description |
|---|---|---|
| `calendar.days` | CalendarPlugin | List of days with events |
| `todo.duedate` | TodoPlugin | Todos grouped by due date |
| `todo.no_duedate` | TodoPlugin | Todos without a due date |
| `owner.name` | OwnerPlugin | Owner's display name |
| `owner.birthday` | OwnerPlugin | Owner's birthday date |
| `owner.birthday_today` | OwnerPlugin | True if today is the owner's birthday |
| `system.user` | SystemPlugin | Current user |
| `system.hostname` | SystemPlugin | Machine hostname |
| `system.os` | SystemPlugin | OS pretty name |
| `image.rml` | ImagePlugin | RML image command string |

These base variables are always available regardless of plugins:

| Variable | Description |
|---|---|
| `today` | Current date |
| `now` | Current time |
| `line_width` | Printer line width in characters (32) |
| `line_single` | Single line rule (`────…`) |
| `line_double` | Double line rule (`════…`) |

Plugin contexts are evaluated lazily — a plugin's `get_context()` is
only called when the template actually accesses one of its variables.

### Jinja2 quick reference

```
{% if condition %}text{% endif %}

{% for item in list %}{{ item }}{% endfor %}

{% extends "base.rml" %}
{% block content %}...{% endblock %}

{% include "footer.rml" %}
```

Use `strftime` for date formatting — format strings documented at [strftime.org](https://strftime.org/).


## Writing plugins

Create a file named `something_plugin.py` containing a class `SomethingPlugin`
that inherits from `rafthercal.plugin.BasePlugin`:

```python
from rafthercal.plugin import BasePlugin

class WeatherPlugin(BasePlugin):
    def get_context(self):
        return {
            'temperature': fetch_temperature(),
            'forecast': fetch_forecast(),
        }
```

Place the file in a directory and point `RAFTHERCAL_PLUGIN_DIR` at it in `config.py`:

```python
RAFTHERCAL_PLUGIN_DIR = "/home/pi/rafthercal/my_plugins"
```

The plugin is then available in templates as `weather.temperature`,
`weather.forecast`, etc. No registration required — any `*_plugin.py`
file in the configured directory is loaded automatically.

Built-in plugins are always loaded from the package. A user plugin with
the same name as a built-in will replace it.
