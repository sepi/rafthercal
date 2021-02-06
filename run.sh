#!/bin/sh
cd /home/pi/rafthercal
# Weather in BXL
./weather.sh
# Todo list
python todo.py | lp -o raw
# Calendar
python cal.py | lp -o raw
# Fortune cookie
fortune -s | cowsay -W 29 | lp -o raw
echo | lp
