from plugin import BasePlugin

class OwnerPlugin(BasePlugin):
    def get_context(self):
        c = self.get_config()
        return {
            'owner_name': c.OWNER_NAME,
        }
