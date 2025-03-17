import datetime

import caldav

from rafthercal.plugin import BasePlugin

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
    with caldav.DAVClient(url=config.CALDAV_URL,
                          username=config.CALDAV_USERNAME,
                          password=config.CALDAV_PASSWORD) as client:
        my_principal = client.principal()
        calendars = my_principal.calendars()
        c = find_calendar(calendars, config.CALDAV_CALENDAR_NAME)
        days = []
        for offset in range(config.CALDAV_CALENDAR_DAYS):
            period_start = today + datetime.timedelta(days=offset)
            period_end = period_start + datetime.timedelta(days=1)
            events_today = c.date_search(start=period_start, end=period_end)

            events = []
            for event in events_today:
                event_data = extract_ev(event)
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
