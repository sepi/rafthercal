import sys
from pprint import pprint
from rafthercal.rafthercal import button_loop, load_context

print("========================================")
print("==== Raf's thermal printer calendar ====")
print("========================================")

if "--dump-context" in sys.argv:
    pprint(load_context())
else:
    button_loop()
