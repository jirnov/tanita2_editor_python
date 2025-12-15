'''
Region wrappers

'''
import Tanita2, Lib.World.Globals
from Tanita2 import vec2


class Region(Tanita2.Region):
    def __init__(self):
        Tanita2.Region.__init__(self)
        self.color = 0x6f0000ff

        # Set attributes
        self.reset()

        # Adding self to global region list
        import Core
        Core.cursor.append(self)



    def set_cursor(self, cursor_state):
        self.cursor = cursor_state


    def process(self, cursor_object, clicked, pressed, released):
        self.over = self.is_inside(cursor_object)
        if self.over:
            self.enter = not self.__entered_before
            self.exit = False
            self.click, self.rclick, self.mclick = clicked
            self.press, self.rpress, self.mpress = pressed
            self.release, self.rrelease, self.mrelease = released
        else:
            self.enter = False
            self.exit = self.__entered_before
            self.release, self.rrelease, self.mrelease = self.press, self.rpress, self.mpress
            self.press = self.rpress = self.mpress = False
            self.click = self.rclick = self.mclick = False
        self.__entered_before = self.over


    def clear(self):
        is_over = self.over
        self.reset()
        self.exit = is_over


    def reset(self):
        # Region flags
        self.over = False
        self.enter = False
        self.exit = False

        # Left button flags
        self.click = False
        self.release = False
        self.press = False

        # Right button flags
        self.rclick = False
        self.rrelease = False
        self.rpress = False

        # Middle button flags
        self.mclick = False
        self.mrelease = False
        self.mpress = False

        self.__entered_before = False


class ZRegion(Tanita2.Region):
    def __init__(self):
        Tanita2.Region.__init__(self)
        self.color = 0x55ff00ff

    def update(self, dt):
        Tanita2.Region.update(self, dt)
        
        for character in Lib.World.Globals.z_region_client_refs:
            character = character()
            if self.is_inside(character) and not character.is_inside_z_region:
                character.parent.update_z_region(character, dt)
        

class BlockRegion(Tanita2.Region):
    def __init__(self):
        Tanita2.Region.__init__(self)
        self.color = 0x22000000
        self.is_active = True

        import weakref
        Lib.World.Globals.block_region_refs.append(weakref.ref(self))

    def enable(self):
        if not self.is_active:
            self.is_active = True

            for walk in Lib.World.Globals.walk_region_refs:
                walk = walk()
                if walk:
                    walk.block_regions.append(self)

    def disable(self):
        if self.is_active:
            self.is_active = False

            for walk in Lib.World.Globals.walk_region_refs:
                walk = walk()
                if walk:
                    if self in walk.block_regions:
                        walk.block_regions.remove(self)


class WalkRegion(Tanita2.PathFindRegion):
    def __init__(self):
        Tanita2.PathFindRegion.__init__(self)
        self.color = 0x22ffff00

        import weakref
        Lib.World.Globals.walk_region_refs.append(weakref.ref(self))
