from datetime import date

from rafthercal.plugin import BasePlugin

class OwnerPlugin(BasePlugin):
    def get_context(self):
        c = self.get_config()
        birthday = date.fromisoformat(c.OWNER_BIRTHDAY) if c.OWNER_BIRTHDAY else None
        birthday_today = False
        if birthday and \
           birthday.month == date.today().month and \
           birthday.day == date.today().day:
            birthday_today = True
        return {
            'owner_name': c.OWNER_NAME,
            'owner_birthday': birthday,
            'owner_birthday_today': birthday_today,
        }
