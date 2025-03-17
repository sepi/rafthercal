from rafthercal.plugin import BasePlugin

import caldav
import icalendar
from datetime import timezone, timedelta, date, datetime
from collections import defaultdict

from .calendar_plugin import find_calendar

def get_todos(config):
    """Fetches todo items from a CalDAV server and structures them by day."""
    client = caldav.DAVClient(config.CALDAV_URL,
                              username=config.CALDAV_USERNAME,
                              password=config.CALDAV_PASSWORD)
    principal = client.principal()
    calendar = find_calendar(principal.calendars(), config.CALDAV_TODO_NAME)

    todos_by_day = defaultdict(list)
    todos_no_day = []
    today = date.today()

    # Fetch todos
    period_start = today
    period_end = period_start + timedelta(days=config.CALDAV_CALENDAR_DAYS)
    for ics in calendar.search(start=period_start, end=period_end,
                               comp_class=caldav.objects.Todo):
        todo = next(filter(lambda comp: isinstance(comp, icalendar.cal.Todo),
                           ics.icalendar_instance.subcomponents), None)
        if todo:
            status = todo.get('status', None)
            due_datetime = todo.get('due', None)

            status = str(status) if status else "UNKNOWN"
            
            todo_dict = {
                "due": getattr(due_datetime, 'dt', None),
                "summary": todo.get('summary', None),
                "description": todo.get('description', None),
                "status": status,
                "completed": status == 'COMPLETED',
                # "location": todo.get('location', None),
                # "geo": todo.get('geo', None),
                "priority": todo.get('priority', None),
                "created": todo.get('created', None),
                "last_modified": todo.get('last_modified', None),
            }
            
            if due_datetime:
                if isinstance(due_datetime.dt, datetime):
                    due_date = due_datetime.dt.date()
                else:
                    due_date = due_datetime.dt
                todos_by_day[due_date].append(todo_dict)
            else:
                todos_no_day.append(todo_dict)

    return todos_by_day, todos_no_day


class TodoPlugin(BasePlugin):
    def get_context(self):
        todo_days_dict, todos_noday = get_todos(self.get_config())
        todo_days = [{'date': date, 'todos': todos} for date, todos in todo_days_dict.items()]
        return {
            'todos_duedate': sorted(todo_days, key=lambda x: x['date']),
            'todos_no_duedate': todos_noday,
        }
