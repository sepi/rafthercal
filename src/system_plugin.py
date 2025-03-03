import os
import platform

from plugin import BasePlugin

class SystemPlugin(BasePlugin):
    def get_context(self):
        un = platform.uname()
        os_release = platform.freedesktop_os_release()
        return {
            'user': os.getenv('USER'),
            'hostname': platform.node(),
            'architecture': platform.architecture(),
            'uname_system': un.system,
            'os': os_release['PRETTY_NAME']
        }
