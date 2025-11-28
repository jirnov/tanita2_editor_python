try:
    from Core import *
    import Lib.World.Globals
except: pass

class Teleport:
    '''
    Jumping zone

    '''
    def __init__(self):
        self.states[self.state].link = self.__empty_link
        self.states[self.state].on_enter = self.__on_enter
        self.is_active = getattr(self, 'is_active', lambda: True)
        self.get_disable_cursor = getattr(self, 'get_disable_cursor', lambda: CURSOR_NORMAL)
        self.__previous_active = None
        self.current_character = triggers.current_character

    def __on_enter(self):
        location = engine.previous_location.name.lower()

        if hasattr(self, 'on_enter'):
            self.on_enter()

        if location:
            if hasattr(self.parent, 'pointKrosh_from_' + location):
                point = getattr(self.parent, 'pointKrosh_from_' + location)
                engine.active_character.position = vec2(point.position)
            if hasattr(self.parent, 'pointEzhik_from_' + location):
                point = getattr(self.parent, 'pointEzhik_from_' + location)
                engine.second_character.position = vec2(point.position)


    def __jump_to_location(self, character=None):
        import Core
        point = getattr(self.parent, 'pointTo_' + self.name[len('Pass_'):])
        if character is None:
            character = Core.active_character
        position = character.absolute_position - point.absolute_position
        if (abs(position.x) + abs(position.y) > 50):
            return
        if hasattr(self, 'before_jump'):
            self.before_jump()
        location = self.name[len('Pass_'):]
        jump_to_location(name = location.capitalize())

    def __zoom_link(self):
        if active_character.seqZoom.is_over:
            self.__jump_to_location()

    def __on_exit(self):
        import Globals, Core
        self.current_character = triggers.current_character
        
        if not Core.active_character.is_busy():
            location = self.name[len('Pass_'):]
            if hasattr(self.parent, 'pointTo_' + location):
                point = getattr(self.parent, 'pointTo_' + location)
                if not Core.active_character.sendTo(point, callback=self.__jump_to_location):
                    # Активный персонаж дойти туда не может. Посылаем второго.
#                    print "WARN: sending second character to junction"
                    Core.second_character.sendTo(point, callback=lambda: self.__jump_to_location(Core.second_character))

    def __empty_link(self):
        active = self.is_active()
        if self.__previous_active is None or active != self.__previous_active:
            self.__previous_active = active
            if active:
                if self.objects.has_key('Magic'):
                    states = list(self.objMagic.states.iterkeys())
                    states.remove('__empty__')
                    self.objMagic.state = states.pop()
                self.regClick.cursor = CURSOR_GOTO
            else:
                if self.objects.has_key('Magic'):
                    self.objMagic.state = '__empty__'
                self.regClick.cursor = self.get_disable_cursor()
        if self.regClick.click and active:
            getattr(self, 'on_exit', self.__on_exit)()
