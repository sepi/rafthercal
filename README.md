# rafthercal

Rafthercal stands for _Raf's thermal printer calendar_. It's a python 3
application that can run on a machine connected to a thermal printer
like the ones used in cash registers. It is primarily meant to print
*calendars* and *todo lists* from CalDav online calendars.

The formatting of the printed output is customizable via
[jinja2](https://jinja.palletsprojects.com/en/stable/templates/)
templates and formatting directives of the [Receipt Markup Language
(RML)](https://github.com/sepi/RML) are accepted to format and style
the output.

In order to provide more _flexiblity_ to the user, the code that
generates or fetches the data to be printed is implemented as plugins,
allowing to implement additional ones without having to modify the
application itself.

By default, the application is started via a button. You can also tap
a certain pattern (like morse) to select between different print
templates. A short press can for example print your todo list while a
long might print the calendar.


## Hardware
The usual hardware to run this project on is a Raspberry Pi. It can
easily interface with a cheap RS232 thermal printer found on chinese
ecommerce sites. It can also easily connect a pushbutton via
GPIO. This can be used to trigger the printing process.


## Installation
In order to install _rafthercal_ on your _Raspberry Pi_, you need to
open a console (eg. via ssh) and enter the following commands.

Go to home directory:

`$ cd`

Create a directory for the project and go there:

`$ mkdir rafthercal && cd rafthercal`

Create a python virtual environment to install the dependencies into:

`$ python3 -m venv venv`

Activate the venv:

`$ . venv/bin/activate`

Install _rafthercal_ and its dependencies into the venv:

`$ python3 -m pip install git+https://github.com/sepi/rafthercal.git`

Congratulations, you have not successfully installed _rafthercal_. Before you can use it, you need to configure it.


## Update
You can update _rafthercal_ by running `$ update-rafthercal`.


## Configuration
In order to configure _rafthercal_, you need to copy the file
`config.py.sample` into your `rafthercal` directory and set up some
important values.

From your `rafthercal` directory, execute:

`$ cp venv/lib/python3*/site-packages/rafthercal/config.py.sample config.py`

You can now edit the file and change the following important values to
your liking:

* `RAFTHERCAL_SERIAL_DEVICE`: The path of the printer device
* `RAFTHERCAL_BUTTON_PIN`: The pin number that is used for a normally
  open button. If none, the application will use the 'Enter' key
  instead. Unfortunately, this only works with X11.
* `RAFTHERCAL_PLUGIN_CLASSES`: Use this to configure the plugins that
  you want to use. Remove any plugins you don't use.
* `CALDAV_SERVERS`: Configure URL, user and password of your caldav
  servers here.
* `CALDAV_CALENDARS`: Configure the calendars you want to include in
  your printout here.
* `CALDAV_TODOS`: Configure the todo lists you want to include in your
  printout here.
  
The configuration file template you previously copied to `config.py` includes comments with more thorough documentation.


## Running _rafthercal_
Once you have finished configuration, you can finally launch the application:

`$ python3 -m rafthercal` or `$ run-rafthercal`

This will put you in a loop waiting for a pattern to be entered via
keyboard or GPIO connected button. To exit, press <Ctrl>-C.

If you want to automatically launch the application when the machine starts, you can install its _systemd_ service file.

`$ mkdir -p $HOME/.config/systemd/user/`

`$ cp venv/lib/python3*/site-packages/rafthercal/rafthercal.service $HOME/.config/systemd/user/`

Now you need to tell systemd to reload its units:

`$ systemctl --user daemon-reload`

Then enable the service so it's actually active:

`$ systemctl --user enable rafthercal`

And finally make it run:

`$ systemctl --user start rafthercal`

Next time you reboot, the service will automatically be started.


## Templates
_rafthercal_ comes with a few templates pre-installed. You can have a look at them in `venv/lib/python3.13/site-packages/rafthercal/templates`.

You can either create your own new templates in the
`rafthercal/templates` directory and reference them in the
`RAFTHERCAL_TEMPLATES` config variable. These new templates can use
the existing templates by extending them or including them.

Whenever you create a template in `rafthercal/templates` with the same
name as a pre-installed template, the new one will override the
installed one.


### How they work
The templates use the
[jinja2](https://jinja.palletsprojects.com/en/stable/templates/)
template language. It uses two constructs to either do control flow
(if-then-else constructs or loops) or display the values of variables
defined by the plugins like the calendar plugin.

You can conditionally display text using: 
```
{% if condition %}
test to display
{% endif %}
```

Variables can be displayed using:
```
{{ variable }}
```

You can extend templates (fill in pre-defined holes in a template with content) using:
```
{% extends "base.rml" %}

{% block some_block %}
the content to be filled into the "hole" with name "some_block" in template "base.rml"
{% endblock %}
```

You can also just include (copy it) into your template using: 
```
{% include "footer.rml" %}
```

### Date formatting
Use strftime to format dates and times using format strings documented [here](https://strftime.org/).


## Implement your own plugins
Create a class `FooPlugin` in a file `foo.py` in the rafthercal directory that inherits from `rafthercal.plugin.BasePlugin` and list it in `RAFTHERCAL_PLUGIN_CLASSES` as `foo.FooPlugin`.  Implement `get_context` and `get_template`.
