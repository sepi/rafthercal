import datetime

import caldav

from rafthercal.plugin import BasePlugin

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

            day = {'date': period_start}
            events = []
            for e in events_today:
                dtstart = e.icalendar_component['DTSTART']
                dtend = e.icalendar_component['DTEND']
                ev = {
                    'summary': e.icalendar_component['SUMMARY'],
                    'location': getattr(e.icalendar_component, 'LOCATION', None),
                    'description': getattr(e.icalendar_component, 'DESCRIPTION', None),
                    'dtstart': dtstart.dt,
                    'dtend': dtend.dt,
                }
                if getattr(dtstart.dt, 'time', False):
                    ev['tstart'] = dtstart.dt.time()
                if getattr(dtend.dt, 'time', False):
                    ev['tend'] = dtend.dt.time()
                events.append(ev)
            day['events'] = events
            days.append(day)
    return days


class CalendarPlugin(BasePlugin):
    def get_context(self):
        return {
            'calendar_days': get_events(self.get_config())
        }
