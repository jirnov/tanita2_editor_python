"""
Main engine module

"""
import sys, Globals, Tanita2, Core

# Script engine
class Engine:
    def construct(self):
        Tanita2.setCursorAcceleration(Tanita2.vec2(2, 2))

        # Module aliases
        import sys
        sys.modules['Core'] = sys.modules['Lib.World.Core']
        sys.modules['Globals'] = sys.modules['Lib.World.Globals']

        self.__versionNumber = Tanita2.TextObject()
        self.__versionNumber.text = "Ver. 0.17"
        self.__versionNumber.color = 0xffff00ff

        # Initialize random generator
        import random
        random.seed()

        self.on_frame = self.normal_on_frame
        self.on_keypress = self.normal_on_keypress

        import Lib
        if Lib.config.has_key('unitest_enable') and Lib.config['unitest_enable']:
            if Lib.config.has_key('unitest_commands'):
                Lib.config['use_startup_location'] = False
                Lib.config['do_profile'] = False
                self.unitest = Core.Unitest(Lib.config['unitest_commands'])
                self.on_frame = self.unitest_on_frame
                self.on_keypress = self.unitest_on_keypress

        # Creating updateable object
        self.location = Tanita2.GameObject()

        # Flag
        Core.location_is_loading = self.location_is_loading = False

        # Set handler
        Core.jump_to_location = self.jump_to_location

        # Creating messages
        Core.messages = self.messages = Core.Messages()

        # Creating environment
        Core.environment = self.environment = Core.Environment()

        # Loading startup location
        self.load_location('Launcher')

        # Register self
        self.messages.register('Engine', self, 'Environment')


    def unload_location(self, name):
        self.environment.begin_unload_location(name)

        # Clear regions
        Core.cursor.clear_group('Default')

        # Clear messages queue
        self.messages.clear()

        # Clear regions
        del Globals.z_region_client_refs[:]
        del Globals.walk_region_refs[:]
        del Globals.block_region_refs[:]

        ### Unload previous location ###
        getattr(self.location, 'begin_unload_location', lambda name: None)(name)

        # Remove location
        del self.location

        import gc
        gsize = len(gc.garbage)
        csize = gc.collect()

        import Lib.Globals
        Lib.Globals.mouse_buttons = 0

        self.environment.end_unload_location()



    def jump_to_location(self, name, use_fadein=True):
        if self.location_is_loading:
            return
        Core.engine.location_is_loading = self.location_is_loading = True
        Core.messages.send('Cursor', 'Disable')
        def opaque_callback():
            self.load_location(name)
            Core.messages.send('Fading', 'doTransparent')
        if use_fadein:
            Core.messages.send('Fading', 'doOpaque', callback=opaque_callback)
        else:
            opaque_callback()


    def load_location(self, name):
        if Core.engine.current_location.name:
            self.unload_location(Core.engine.current_location.name)
            Core.engine.current_location.name = None
        self.environment.begin_load_location(name)
        location_module = getattr(__import__('World.%s' % name, name), name)
        self.location = getattr(location_module, name)()
        self.location.end_load_location()
        self.environment.end_load_location(name)
        Core.engine.location_is_loading = self.location_is_loading = False


    def save_game(self):
        self.environment.save()


    def load_game(self, params):
        if Core.engine.current_location.name:
            self.unload_location(Core.engine.current_location.name)
        self.environment.begin_load_game(params)
        name = Core.engine.current_location.name
        self.environment.begin_load_location(name)
        location_module = getattr(__import__('World.%s' % name, name), name)
        self.location = getattr(location_module, name)()
        self.environment.end_load_game(params)
        self.location.end_load_location()
        self.environment.end_load_location(name)
        self.location.end_load_game(params)


    def normal_on_frame(self, dt):
        self.environment.begin_update(dt)
        self.location.update(dt)
        self.environment.end_update(dt)
        #self.__versionNumber.update(dt)


    def on_cleanup(self):
        pass


    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'LoadLocation':
            self.load_location(kwargs['name'])
            return True
        if msg_id == 'LoadGame':
            self.load_game(kwargs['params'])
            return True
        if msg_id == 'SaveGame':
            self.save_game()
            return True


    def normal_on_keypress(self, keycode):
        if Core.engine.keyboard.is_enabled and keycode in (27, 32, 13):
            self.messages.send_all('on_keypress', keycode=keycode)


    def unitest_on_keypress(self, keycode):
        pass


    def unitest_on_frame(self, dt):
        import Lib.Globals
        from Core import vec2
        Lib.Globals.cursor_position = vec2(-1024, -1024)
        Lib.Globals.mouse_buttons = 0
        self.unitest.update(dt)
        self.normal_on_frame(dt)


# Creating instance
_engine = Engine()
