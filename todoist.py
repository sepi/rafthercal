from __future__ import print_function
from todoist.api import TodoistAPI
from Adafruit_Thermal import *
import dateutil.parser
import unicodedata
import config

api = TodoistAPI(config.todoist_token)
api.sync()

p = Adafruit_Thermal()
p.setDefault()
p.setSize('L')
p.println('Todo')

for i in api.items.all():
    # print(i)

    date_str = i['due']
    if date_str:
        date_str = date_str['date']
    if date_str:
        due_date = dateutil.parser.parse(date_str)
    else:
        due_date = None

    p.boldOn()
    p.underlineOn()
    p.justify('L')
    p.print('[ ] ')
    if due_date:
        p.println(due_date.strftime(config.date_format))
    else:
        p.println('')

    p.boldOff()
    p.underlineOff()

    p.justify('R')

    content = unicodedata.normalize(
        'NFD', i['content']).encode('ascii', 'ignore')
    p.println(content)

    #print(i['content'], i['date_completed'], due_date)
