from Tanita2 import Location as LocationBase, vec2, Region
from Overrides import Location as UserLocation


class Location(LocationBase, UserLocation):
    def __init__(self):
        LocationBase.__init__(self)
        self.__cameraState = 'Freehand'
        self.__cameraTarget = None
        self.__cameraSpeed = 0
        self.__minDistance = 50
        self.__firstTime = True
        self.__dt = [0] * 10
        self.__width = 1024
        self.__height = 768
        self.__name = ""
        self.__backupSounds = {}
        self.position = vec2(0, 0)
        self.update = self.on_update
        from Core import messages
        if messages.has_key('Location', 'Environment'):
            messages.unregister('Location', 'Environment')
        messages.register('Location', self, 'Environment')


    def get_name(self):
        return self.__name


    def set_name(self, value):
        self.__name = value
        from Core import engine
        engine.current_location.name = self.__name


    def get_width(self):
        return self.__width


    def set_width(self, value):
        self.__width = value
        from Core import engine
        engine.current_location.width = self.__width


    def get_height(self):
        return self.__height


    def set_height(self, value):
        self.__height = value
        from Core import engine
        engine.current_location.height = self.__height


    width = property(get_width, set_width)
    height = property(get_height, set_height)
    name = property(get_name, set_name)


    def end_load_location(self, location_name=None):
        UserLocation.__init__(self)
        Location.update_block_regions()


    def end_load_game(self, params):
        self.position = vec2(*params['current_location.position'])


    def begin_unload_location(self, location_name=None):
        UserLocation.begin_unload_location(self, location_name)
        Location.forceUnload(self)


    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'Disable':
            self.update = lambda dt: None
            return True
        if msg_id == 'Enable':
            self.update = self.on_update
            return True
        if msg_id == 'backupPlayingSounds':
            self.__backupSounds = {}
            def stop_sound(obj):
                for o in getattr(obj, 'objects', {}).itervalues():
                    stop_sound(o)
                for snd in getattr(obj, 'sounds', {}).itervalues():
                    self.__backupSounds[snd] = (snd.volume, snd.is_playing)
                    if snd.is_playing:
                        snd.stop()
                    snd.volume = 0
            stop_sound(self)
            return True

        if msg_id == 'restorePlayingSounds':
            for snd, (volume, is_playing) in self.__backupSounds.iteritems():
                snd.volume = volume
                if is_playing:
                    snd.play()
            self.__backupSounds = {}
            return True



    @staticmethod
    def forceUnload(object):
        if not hasattr(object, 'objects'):
            return
        
        for obj in object.objects.itervalues():
            Location.forceUnload(obj)
        object.objects.clear()
        object._release()
        
        if not isinstance(object, Region):
            for attrname in object.__dict__.copy().iterkeys():
                delattr(object, attrname)
        
        if hasattr(object, 'states'):
            for state in object.states.itervalues():
                state.on_enter = state.on_update = state.on_exit = state.link = None
            object.states.clear()
        
        if hasattr(object, 'sequences'):
            object.sequences.clear()
        
        if hasattr(object, 'sounds'):
            for sound in object.sounds.itervalues():
                sound.stop()
            object.sounds.clear()
        del object
        
    
    # Attaching block regions to walk regions
    @staticmethod
    def update_block_regions():
        import Lib.World.Globals
        for walk in Lib.World.Globals.walk_region_refs:
            walk = walk()
            if not walk: continue

            walk.block_regions = []
            for block in Lib.World.Globals.block_region_refs:
                if not block() or not block().is_active: continue
                walk.block_regions.append(block())


    def magicFormula(self):
        dist = self.__cameraTarget.position.x + self.position.x - 512
        return dist


    def distanceToCameraTarget(self):
        return abs(self.__cameraTarget.position.x + self.position.x - 512)


    def update_position(self, dt):
        self.__dt[:9] = self.__dt[1:]
        self.__dt[-1] = dt
        dt = sum(self.__dt) / 10

        # For floating locations
        import Core
        from Core import triggers
        
        character = Core.active_character
        character2 = Core.second_character

        if self.__firstTime:
            if character:
                self.position.x = -character.position.x + 512
                self.__cameraState = 'onCharacter'
                self.__cameraTarget = character
            self.__firstTime = False

        if not character:
            self.__cameraState = 'Freehand'
            self.__cameraTarget = None
            self.__cameraSpeed = 0
        else:
            if self.__cameraState == 'Freehand':
                self.__cameraTarget = character

                if self.distanceToCameraTarget() < self.__minDistance:
                    self.__cameraState = 'onCharacter'
                    self.__cameraSpeed = 0
                else:
                    self.__cameraState = 'Moving'
                    self.__cameraSpeed = self.magicFormula()

            elif self.__cameraState == 'Moving':
                assert self.__cameraTarget

                if character is not self.__cameraTarget:
                    self.__cameraTarget = character

                if self.distanceToCameraTarget() < self.__minDistance:
                    self.__cameraState = 'onCharacter'
                    self.__cameraSpeed = 0
                else:
                    self.__cameraSpeed = self.magicFormula()

            elif self.__cameraState == 'onCharacter':
                assert self.__cameraTarget

                if character is not self.__cameraTarget:
                    self.__cameraTarget = character

                if self.distanceToCameraTarget() < self.__minDistance:
                    self.__cameraState = 'onCharacter'
                    self.__cameraSpeed = 0
                else:
                    self.__cameraState = 'Moving'
                    self.__cameraSpeed = self.magicFormula()

            else:
                assert False, "Unknown camera state: " + self.__cameraState

        self.position.x -= dt * self.__cameraSpeed
        if self.position.x > 0:
            self.position.x = 0
        if self.position.x < -self.__width + 1024:
            self.position.x = -self.__width + 1024


    def on_update(self, dt):
        import Core
        self.update_position(dt)
        
        Core.engine.current_location.position.x = self.position.x
        Core.engine.current_location.position.y = self.position.y

        # Resetting z region processing flags
        import Globals
        for c in Globals.z_region_client_refs:
            c = c()
            if not c: continue
            c._z_processed__ = False

        # Updating children (with parallax)
        self.begin_update()
        for o in self.objects.itervalues():
            parallax = getattr(o, 'parallax', vec2(1, 1))
            o.position.x = int(self.position.x * parallax.x)
            o.position.y = int(self.position.y * parallax.y)
            o.update(dt)
        self.end_update()
