class DictContainer:
    def __init__(self):
        self.__dict__['__children__'] = {}


    def isEmpty(self):
        return len(self.__dict__['__children__']) == 0


    def setValue(self, name, value):
        self.__dict__['__children__'][name] = value


    def __getattr__(self, name):
        if name not in self.__dict__['__children__']:
            self.__dict__['__children__'][name] = DictContainer()
        return self.__dict__['__children__'][name]


    def __eq__(self, value):
        return value is None


    def __ne__(self, value):
        return not value is None


    def __nonzero__(self):
        return False


    def __str__(self):
        return str(None)


    def iterkeys(self):
        return self.__dict__['__children__'].iterkeys()


    def itervalues(self):
        return self.__dict__['__children__'].itervalues()


    def iteritems(self):
        return self.__dict__['__children__'].iteritems()

    def clear(self):
        return self.__dict__['__children__'].clear()

    def __setattr__(self, name, value):
        if name in self.__dict__['__children__']:
            if isinstance(self.__dict__['__children__'][name], DictContainer):
                if not self.__dict__['__children__'][name].isEmpty():
                    names = list(self.__dict__['__children__'][name].iterkeys())
                    raise AttributeError, "You try to remove childrens (%s) with setattr!" % names
        self.__dict__['__children__'][name] = value


    def dump(self):
        children = []
        names = list(self.__dict__['__children__'].iterkeys())
        names.sort()
        for name in names:
            value = self.__dict__['__children__'][name]
            if isinstance(value, DictContainer):
                dump = value.dump()
                if dump:
                    children.append({'__name__' : name, '__values__' : dump})
            elif not value is None:
                children.append({'__name__' : name, '__value__' : value})
        children.sort()
        return children


    def restore(self, children):
        self.__dict__['__children__'] = {}
        for dictionary in children:
            name = dictionary['__name__']
            if '__values__' in dictionary:
                self.__dict__['__children__'][name] = DictContainer()
                self.__dict__['__children__'][name].restore(dictionary['__values__'])
                continue
            if '__value__' in dictionary:
                self.__dict__['__children__'][name] = dictionary['__value__']


    def printf(self, prefix):
        names = list(self.__dict__['__children__'].iterkeys())
        names.sort()

        for name in names:
            value = self.__dict__['__children__'][name]
            if isinstance(value, DictContainer):
                value.printf('%s.%s' % (prefix, name))
            else:
                print '%s.%s = %s' % (prefix, name, repr(value))


class GameTriggers(DictContainer):
    def __init__(self):
        DictContainer.__init__(self)

        from Core import settings
        if settings.steady_data.has_key('heroes'):
            self.heroes.restore(settings.steady_data['heroes'])
        else:
            self.heroes.all = ('Kopatich', 'Losyash', 'Sovunya', 'Nusha', 'Krosh', 'Karich', 'Ezhik', 'Barash', 'Pin')
            self.heroes.opened = []
            self.heroes.visited = ['Krosh', 'Ezhik']
            settings.steady_data['heroes'] = self.heroes.dump()

        self.launcher.tray_disabled = True



        import Lib
        if Lib.config.has_key('triggers'):
            for key, value in Lib.config['triggers'].iteritems():
                names = key.split(".")
                if len(names) == 0:
                    setattr(self, key, value)
                else:
                    parent = None
                    for i, name in enumerate(names):
                        if i == 0:
                            parent = getattr(self, name)
                        elif i < len(names) - 1:
                            parent = getattr(parent, name)
                    setattr(parent, names[-1], value)


    def printf(self):
        DictContainer.printf(self, 'triggers')




class EngineTriggers(DictContainer):
    def __init__(self):
        DictContainer.__init__(self)

        self.current_location.name = ''
        self.current_location.width = 1024
        self.current_location.height = 768
        self.current_location.position.x = 0
        self.current_location.position.y = 0

        import Lib
        if Lib.config.has_key('tray_items'):
            self.tray_items = list(Lib.config['tray_items'])
        else:
            self.tray_items = []

        self.previous_location.name = ''


    def printf(self):
        DictContainer.printf(self, 'engine')



class Triggers:
    def __init__(self):
        self.game = GameTriggers()
        self.engine = EngineTriggers()


    def begin_load_location(self, location_name=None):
        self.game.previous_location.name = self.game.current_location.name
        self.game.current_location.name = location_name


    def begin_save_game(self, params):
        from Core import messages, settings
        messages.send('characterController', 'savePosition')
        from time import localtime
        params['date'] = localtime()
        params['current_location.name'] = self.engine.current_location.name
        params['current_location.position'] = (self.engine.current_location.position.x, self.engine.current_location.position.y)
        params['previous_location.name'] = self.engine.previous_location.name
        import Core
        if Core.active_character is not None:
            params['active_character.position'] = (self.engine.active_character.position.x, self.engine.active_character.position.y)
        if Core.second_character is not None:
            params['second_character.position'] = (self.engine.second_character.position.x, self.engine.second_character.position.y)
        params['cursor_color'] = self.engine.cursor.color
        params['tray_items'] = (self.engine.tray_items is None and [[]] or [list(self.engine.tray_items)]).pop()
        params['triggers'] = self.game.dump()
        settings.steady_data['heroes'] = self.game.heroes.dump()


    def begin_load_game(self, params):
        self.game.restore(params['triggers'])
        from Core import settings
        self.game.heroes.restore(settings.steady_data['heroes'])
        self.engine.tray.is_disabled = False
        self.game.current_location.name = self.game.previous_location.name
        self.engine.current_location.name = params['current_location.name']
        self.engine.previous_location.name = params['previous_location.name']


    def end_load_game(self, params):
        from Core import vec2, messages, timer
        if 'active_character' in params:
            self.engine.active_character.position = vec2(*params['active_character.position'])
        if 'second_character' in params:
            self.engine.second_character.position = vec2(*params['second_character.position'])
        messages.send('Cursor', 'SetColor', params['cursor_color'])
        timer.append(0, lambda: messages.send_all('GameLoaded'))


    def end_load_location(self, location_name=None):
        if location_name:
            setattr(getattr(self.game, location_name.lower()), 'is_visited', True)
        if location_name == 'Launcher' or self.engine.previous_location.name == 'Launcher':
            return
        import Lib
        if Lib.config.has_key('use_startup_location') and Lib.config['use_startup_location']:
            return
        from Core import environment, settings
        environment.save()
