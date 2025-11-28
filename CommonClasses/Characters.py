class Characters:
    '''
    Characters metaobject
    '''
    
    def __init__(self):
        import Core
        Core.messages.register("characterController", self)
        self.update = self.on_update
        for character in self.objects.itervalues():
            if not hasattr(character, '_shouldBeCreated'):
                character._shouldBeCreated = lambda: True
        
    
    def on_message(self, msgid, **kwargs):
        if msgid == "photoActivate":
            import Core
            character = Core.active_character
            if Core.triggers.current_character == 'Ezhik':
                character = Core.second_character
            character.stopMovement()
            def callback():
                character.stateFoto_empty.on_exit = lambda: None
                ani = 'Krosh_photo%d_' % (1 + Core.randint(0, 1000) % 5)
                Core.timer.append(0, lambda: character.sendTo(point=character, targetState=ani))
            character.stateFoto_empty.on_exit = callback
            character.sendTo(point=character, targetState='Foto_empty')
            return True
        if msgid == "zoomActivate":
            import Core
            character = Core.active_character
            if Core.triggers.current_character == "Krosh":
                character = Core.second_character
            if character is None:
                return
            character.stopMovement()
            def callback():
                character.stateLupa.on_exit = lambda: None
                ani = 'Jozh_look%d_' % (1 + Core.randint(0, 1000) % 5)
                Core.timer.append(0, lambda: character.sendTo(point=character, targetState=ani))
            character.stateLupa.on_exit = callback
            character.sendTo(point=character, targetState='Lupa')
            return True
        if msgid == "savePosition":
            import Core
            if Core.active_character:
                Core.engine.active_character.position = Core.vec2(Core.active_character.position)
            if Core.second_character:
                Core.engine.second_character.position = Core.vec2(Core.second_character.position)
            return True
        if msgid == "on_click":
            import Core
            if kwargs['click'] and not Core.environment.dialog.is_shown():
                Core.messages.send('Tray', 'Hide')
                result = Core.active_character.sendToAnywhere(Core.cursor)
                if not result:
                    pass
#                    print "WARN: path could not be found"
                return result

            if kwargs['rclick'] and Core.engine.menu.is_disabled:
                self.__switchCharacters()
            return True
        if msgid == "switch_characters":
            self.__switchCharacters()
            return True
        if msgid == "force_switch_characters":
            self.__switchCharacters(True)
            return True
        
    
    def __switchCharacters(self, force=False):
        import Core
        if Core.second_character.name != 'Shadow' and not Core.second_character.isStunned() and \
           (not Core.environment.dialog.is_shown() or force):
            cursor = {'Krosh' : 'Blue',
                      'Ezhik' : 'Violet'}
            Core.active_character.stopMovement()
            Core.active_character, Core.second_character = Core.second_character, Core.active_character
            Core.triggers.current_character = Core.active_character.name
            Core.cursor.set_color(cursor[Core.triggers.current_character])

            flag = Core.active_character.name == 'Ezhik'                
            Core.messages.send('Tray.Zoom', 'Show', flag)
            Core.messages.send('Tray.Photo', 'Show', not flag)

        
    
    def createCharacter(self, name):
        # Создаем гибрид из CommonCharacter, персонажа из World.Common и персонажа на локации.
        import Overrides.CommonCharacter
        moduleName = 'World.Common.LayerLayer.%sPackage' % name
        baseClassModule = __import__(moduleName)
        baseClassModuleNameParts = moduleName.split('.')
        # Хак, загружающий нужный модуль (__import__ загрузит только самый верхний)
        for part in baseClassModuleNameParts[1:]:
            baseClassModule = getattr(baseClassModule, part)
        baseClass = baseClassModule.__dict__[name]
        
        userClass = self.objects[name].__class__
        
        class Frankenstein(baseClass, userClass, Overrides.CommonCharacter.CommonCharacter):
            def construct(self):
                baseClass.construct(self)
                userClass.construct(self)
                Overrides.CommonCharacter.CommonCharacter.construct(self)
                
            def update(self, dt):
                Overrides.CommonCharacter.CommonCharacter.update(self, dt)
        
        self.objects[name].update(0)
        
        character = Frankenstein()
        if self.objects.has_key(name):
            obj = self.objects[name]
            del self.objects[name]
            delattr(self, 'obj' + name)
            from Core import Location
            Location.forceUnload(obj)

        self.objects[name] = character
        character.name = name
        return character
        
    
    def on_update(self, dt):
        objects = list(self.objects.itervalues())
        objects.sort(lambda a, b: cmp(a.position.y, b.position.y))
        for obj in objects:
            obj.update(dt)
        
    def update_z_region(self, character, dt):
        chars = list(self.objects.itervalues())
        chars.sort(lambda a, b: cmp(a.position.y, b.position.y))
        for char in chars:
            if not getattr(char, 'is_inside_z_region', False):
                char.update(dt)
            char.is_inside_z_region = True
            if char is character:
                break
