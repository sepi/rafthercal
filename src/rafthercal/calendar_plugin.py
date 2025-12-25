import datetime

import caldav

from rafthercal.plugin import BasePlugin
from rafthercal.config_helpers import config_expand

def fill_event(component):
    return {
        'summary': component.get("summary"),
        'description': component.get("description"),
        'dtstart': component.get("dtstart").dt,
        'dtend': component.get("dtend").dt,
        'location': component.get("location"),
    }


def extract_ev(event):
    for component in event.icalendar_instance.walk():
        if component.name == "VEVENT":
            return fill_event(component)


def find_calendar(cals, name):
    return list(filter(lambda c: c.name == name, cals))[0]


def get_events(config):
    today = datetime.date.today()
    days = []
    config_expand(config)
    for server in config.CALDAV_SERVERS:
        with caldav.DAVClient(url=server['url'],
                              username=server['username'],
                              password=server['password']) as client:
            my_principal = client.principal()
            calendars = my_principal.calendars()
            for calendar in config.CALDAV_CALENDARS:
                if calendar['server'] != server['id']:
                    continue # Only consider calendars on this server
                calendar_name = calendar['caldav_name']
                c = find_calendar(calendars, calendar_name)

                for offset in range(calendar['days']):
                    period_start = datetime.datetime.combine(today + datetime.timedelta(days=offset),
                                                             datetime.datetime.min.time())
                    period_end = datetime.datetime.combine(period_start + datetime.timedelta(days=1),
                                                           datetime.datetime.min.time())
                    events_today = c.date_search(start=period_start, end=period_end)
        
                    events = []
                    for event in events_today:
                        event_data = extract_ev(event)
                        event_data['calendar_id'] = calendar['id']
                        event_data['server_id'] = server['id']
                        events.append(event_data)
        
                    if events:
                        days.append({'date': period_start,
                                     'events': events})
    return days


class CalendarPlugin(BasePlugin):
    def get_context(self):
        return {
            'calendar_days': get_events(self.get_config())
        }
