'''
Location initialization.
Location.__init__ method called at the end of location loading
so all child and global objects are available.

'''
class Location:
    def __init__(self):
        import Core
        
        # Добавляем в engine точки под именами.
        for layername, layer in self.objects.iteritems():
            for pointname, point in layer.objects.iteritems():
                if isinstance(point, Core.Point):
                    if pointname.startswith('Safe_'):
                        setattr(Core.engine.safe_points, pointname, point)
                    else:
                        setattr(Core.engine.points, pointname, point)

        if Core.active_character:
            from Core import Location
            Location.forceUnload(Core.active_character)
            Core.active_character = None

        if Core.second_character:
            from Core import Location
            Location.forceUnload(Core.second_character)
            Core.second_character = None
        
        # Добавляем персонажей.
        if self.objects.has_key('Characters'):
            # Если на локации нет слоя Characters, то и персонажей быть не может.
            if not self.objects.has_key('Characters'):
#                print "Location doesn't have 'Characters' layer."
                return
            
            
            # Если слой Characters есть, у него должен быть объект Characters c
            # как минимум одним подобъектом Krosh.
            charactersLayer = self.objects['Characters']
            assert charactersLayer.objects.has_key('Characters')
            characters = charactersLayer.objects['Characters']
            
            # Один персонаж (Крош) у нас должен быть всегда.
            assert characters.objects.has_key("Krosh")
            characters.objKrosh.states[characters.objKrosh.state].on_exit = lambda: None
            characters.objKrosh.state = '__empty__'
            Core.active_character = characters.createCharacter("Krosh")
            Core.active_character.position = Core.vec2(400, 100)

            do_create_shadow = False

            # Если Йожег есть в списке объектов, то создаем и второго персонажа.
            if characters.objects.has_key('Ezhik'):
                characters.objEzhik.states[characters.objEzhik.state].on_exit = lambda: None
                characters.objEzhik.state = '__empty__'
                if characters.objEzhik._shouldBeCreated():
                    Core.second_character = characters.createCharacter("Ezhik")
                    Core.second_character.position = Core.vec2(600, 100)
                else:
                    characters.objEzhik.state = '__empty__'
                    do_create_shadow = True
            else:
                do_create_shadow = True

            if do_create_shadow:
                # Йожега на этой локации нет. Создаем объект - дух Йожега.
                import Tanita2
                class Shadow(Tanita2.GameObject):
                    def __init__(self):
                        Tanita2.GameObject.__init__(self)
                        self.name = 'Shadow'
                        self.position = Tanita2.vec2(-10000, -10000)
                    def construct(self): pass
                    def is_busy(self): return False
                    def stopMovement(self): pass
                    def update(self): pass
                    def sendTo(self, point, callback=lambda: None, targetState='Stay'): return False
                    def _enableBlockRegion(self, enable): pass
                Core.second_character = Shadow()
                Core.triggers.current_character = None
            
            # Сохраняем имя текущего персонажа.
            if not Core.triggers.current_character:
                Core.triggers.current_character = Core.active_character.name
            else:
                if Core.triggers.current_character == 'Ezhik' and Core.second_character.name == 'Ezhik':
                    Core.active_character, Core.second_character = Core.second_character, Core.active_character
                    Core.cursor.set_color('Violet')
                else:
                    Core.cursor.set_color('Blue')
            
            # Восстанавливаем позицию персонажей.
            from Core import engine, vec2
            if engine.active_character.position:
                Core.active_character.position = vec2(engine.active_character.position)
            
            if Core.second_character is not None and engine.second_character.position:
                Core.second_character.position = vec2(engine.second_character.position)
            engine.active_character.position = engine.second_character.position = None
        
    
    def begin_unload_location(self, location_name=None):
        from Core import engine
        engine.previous_location.name = location_name
        for name in engine.points.iterkeys():
            setattr(engine.points, name, None)
        engine.points.clear()
        
        for name in engine.safe_points.iterkeys():
            setattr(engine.safe_points, name, None)
        engine.safe_points.clear()
        
