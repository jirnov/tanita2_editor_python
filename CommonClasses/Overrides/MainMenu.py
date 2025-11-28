from Tanita2 import GameObject
from Core import messages, engine, triggers
'''
Main and ingame menu

'''

__all__ = ['MainMenu']


class MainMenu(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        self.main_layer = self.objects['Main'] = GameObject()
        from World.Interface_common.CommonLayer import CommonLayer
        messages.send('Cursor', 'ChangeLoadGroup', 'Menu')
        self.common = self.objects['Common'] = CommonLayer()
        messages.send('Cursor', 'ChangeLoadGroup', 'Default')
        self.buttons = None
        self.last_direction = 'Left'
        self.update = lambda dt: None
        self.__cursorFlags = None
        engine.menu.is_enabled = False
        engine.menu.is_disabled = True
        messages.register('Menu', self, 'Environment')


    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'Disable':
            if not engine.menu.is_disabled:
                self.update = lambda dt: None
            return True

        if msg_id == 'Enable':
            if not engine.menu.is_enabled:
                try:
                    del self.update
                except AttributeError:
                    pass
            return True

        if msg_id == 'Show':
            self.show(*args, **kwargs)
            return True

        if msg_id == 'Hide':
            self.hide(*args, **kwargs)
            return True

        if msg_id == 'on_keypress':
            if engine.location_is_loading:
                return
            
            if engine.current_location.name == 'Launcher':
                return

            if engine.video.is_playing:
                return
            
            if engine.dialog.is_working:
                return
            
            if engine.menu.is_disabled:
                messages.send('Music', 'ChangeDisk', 'Menu')
                self.show(saveCursorFlags=True, backupPlayingSounds=True)
                return True
                
            if engine.menu.is_enabled:
                messages.send('Music', 'ChangeDisk', 'Game')
                self.hide(restoreCursorFlags=True, restorePlayingSounds=True)
                return True

        if msg_id == 'ChangeLayer':

            messages.send('Cursor', 'Disable')

            engine.keyboard.is_enabled = False

            hide_buttons = engine.fading.is_transparent

            def transparent_callback():
                engine.keyboard.is_enabled = True
                direction = self.last_direction == 'Left' and 'Right' or 'Left'
                self.last_direction = direction
                messages.send('MenuTray', 'Move', direction=direction, appear=True, callback=lambda: messages.send('Cursor', 'Enable'))

            def opaque_callback():
                self.load_layer(kwargs['name'])
                messages.send('Fading', 'doTransparent', callback=transparent_callback)

            def fading_opaque():
                messages.send('Fading', 'doOpaque', callback=opaque_callback)

            if hide_buttons:
                messages.send('MenuTray', 'Move', direction=self.last_direction, callback=fading_opaque)
            else:
                opaque_callback()
            return True

        if msg_id == 'InternalCommand':
            command = kwargs['command']
            if command == 'SetButtons':
                self.buttons = kwargs['buttons']
                return True


    def show_buttons(self, callback=None):
        direction = self.last_direction == 'Left' and 'Right' or 'Left'
        self.last_direction = direction
        callback = (callback is None and [lambda: None] or [callback]).pop()
        messages.send('MenuTray', 'Move', direction=direction, appear=True, callback=callback)


    def hide_buttons(self, callback=None):
        callback = (callback is None and [lambda: None] or [callback]).pop()
        messages.send('MenuTray', 'Move', direction=self.last_direction, callback=callback)


    def show(self, saveCursorFlags=False, backupPlayingSounds=False):
        if not engine.menu.is_disabled:
            return

        import Core
        if Core.active_character:
            Core.active_character.stopMovement()
        if Core.second_character:
            Core.second_character.stopMovement()

        if engine.current_location.name != 'Launcher':
            from Core import environment
            environment.save()

        self.__cursorFlags = [bool(engine.cursor.is_disabled), str(engine.cursor.color)]

        messages.send('Cursor', 'Disable')
        messages.send('Cursor', 'SetColor', 'Menu')
        messages.send('Timer', 'Pause')

        engine.menu.is_disabled = False
        engine.keyboard.is_enabled = False

        messages.send('Cursor', 'BackupGroups', 'Menu')
        messages.send('Cursor', 'EnableGroups', ['Menu'])


        def buttons_callback():
            engine.keyboard.is_enabled = True
            messages.send('Cursor', 'Enable')

        def transparent_callback():
            engine.menu.is_enabled = True
            self.show_buttons(callback=buttons_callback)

        def opaque_callback():
            if backupPlayingSounds:
                messages.send('Location', 'backupPlayingSounds')
            self.__cursorFlags.append(bool(engine.cursor.is_waiting))
            messages.send('Cursor', 'WaitEnable', False)
            messages.send('Location', 'Disable')
            self.load_layer('Main')
            try:
                del self.update
            except AttributeError:
                pass
            messages.send('Fading', 'doTransparent', callback=transparent_callback)

        if engine.fading.is_transparent:
            messages.send('Fading', 'doOpaque', callback=opaque_callback, with_sound=True)
        else:
            opaque_callback()



    def hide(self, restoreCursorFlags=False, restorePlayingSounds=False, callback=None):
        if not engine.menu.is_enabled:
            return

        messages.send('Cursor', 'Disable')

        engine.menu.is_enabled = False
        engine.keyboard.is_enabled = False

        def transparent_callback():
            engine.menu.is_disabled = True
            engine.keyboard.is_enabled = True
            disable_cursor = False
            if restoreCursorFlags and self.__cursorFlags:
                disable_cursor = self.__cursorFlags[0]
                messages.send('Cursor', 'SetColor', self.__cursorFlags[1])
                messages.send('Cursor', 'WaitEnable', self.__cursorFlags[2])
            if restorePlayingSounds:
                messages.send('Location', 'restorePlayingSounds')
            self.__cursorFlags = None
            if not disable_cursor:
                messages.send('Cursor', 'Enable')

        def opaque_callback():
            self.update = lambda dt: None
            self.unload_layer()
            messages.send('Timer', 'Resume')
            messages.send('Cursor', 'RestoreGroups', 'Menu')
            messages.send('Location', 'Enable')
            if callback:
                transparent_callback()
                callback()
            else:
                messages.send('Fading', 'doTransparent', callback=transparent_callback)

        if engine.fading.is_transparent:
            self.hide_buttons(callback=lambda: messages.send('Fading', 'doOpaque', callback=opaque_callback))
        else:
            opaque_callback()


    def unload_layer(self):
        messages.send('Interface.Sounds', 'Stop')
        messages.clear('Interface')
        from Core import Location
        for object in list(self.main_layer.objects.itervalues()):
            Location.forceUnload(object)
        self.main_layer.objects.clear()
        import gc
        gc.collect()


    def load_layer(self, name):
        self.unload_layer()
        name = name.capitalize()
        layer_name = '%sLayer' % name
        module = __import__('World.Interface_%s.%s' % (name.lower(), layer_name), globals(), locals(), [layer_name])

        self.buttons = None

        messages.send('Cursor', 'ClearGroup', 'Menu')
        messages.send('Cursor', 'ChangeLoadGroup', 'Menu')
        messages.enable_forcibly_pool('Interface')
        self.main_layer.objects[name] = getattr(module, layer_name)()
        messages.disable_forcibly_pool()
        messages.send('Cursor', 'ChangeLoadGroup', 'Default')
