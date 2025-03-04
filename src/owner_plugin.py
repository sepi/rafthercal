from datetime import date

from plugin import BasePlugin

class OwnerPlugin(BasePlugin):
    def get_context(self):
        c = self.get_config()
        return {
            'owner_name': c.OWNER_NAME,
            'owner_birthday': date.fromisoformat(c.OWNER_BIRTHDAY) if c.OWNER_BIRTHDAY else None,
        }
