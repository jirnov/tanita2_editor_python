from Tanita2 import GameObject
from Core import vec2, triggers, Region


class Tray(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        from World.Common.AlongLayer import AlongLayer
        self.along = self.objects['Along'] = AlongLayer()
        self.along.position = vec2(0, 0)
        from World.Common.TrayLayer import TrayLayer
        self.tray = self.objects['Tray'] = TrayLayer()
        self.tray.position = vec2(0, 0)


    def disable_regions(self):
        def disable_region(obj):
            for o in getattr(obj, 'objects', {}).itervalues():
                if isinstance(o, Region) and not hasattr(o, 'previous_cursor'):
                    o.previous_cursor = o.cursor
                    o.cursor = 0
                disable_region(o)
        disable_region(self)


    def enable_regions(self):
        def enable_region(obj):
            for o in getattr(obj, 'objects', {}).itervalues():
                if isinstance(o, Region) and hasattr(o, 'previous_cursor'):
                    o.cursor = o.previous_cursor
                    del o.previous_cursor
                enable_region(o)
        enable_region(self)


    def end_load_location(self, location_name=None):
        if getattr(triggers, location_name.lower()).tray_disabled:
            self.disable_regions()
            self.update = lambda dt: None
        else:
            self.enable_regions()
            try:
                del self.update
            except AttributeError:
                pass
