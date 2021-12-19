#!/bin/sh
cd /home/pi/rafthercal
# Weather in BXL
./weather.sh
# Todo list
python google_tasks.py | lp -o raw
# Calendar
python google_cal.py | lp -o raw
# Fortune cookie
#fortune -s | cowsay -W 29 | lp -o raw
echo | lp
