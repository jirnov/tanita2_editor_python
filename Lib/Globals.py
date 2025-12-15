'''
Globals mudule.
Module intended to keep all volatile variables and
values to be keeped after script reloading and cleanups.
'''
from Tanita2 import vec2
import Tanita2

# Cursor position in location coordinates (with respect to zoom and location pos)
cursor_position = vec2(0, 0)

# Zoom factor
zoom = 1

# Current location object and path
class DummyLocation: position = vec2(0, 0)

location = DummyLocation
location_path = ''

# Mouse button state
mouse_buttons = 0
# Mouse position in screen coordinates (without respect to location position)
mouse_position = vec2(0, 0)
