class Environment:
    def __init__(self):
        '''
        Initialize environment

        '''
        import Core

        self.__childrens = []

        from Core import Settings
        Core.settings = self.settings = Settings()

        from Core import Timer
        Core.timer = self.timer = Timer()
        self.__childrens.append(self.timer)

        from Triggers import Triggers
        self.triggers = Triggers()
        self.__childrens.append(self.triggers)
        Core.triggers = self.triggers.game
        Core.engine = self.triggers.engine


        from Core import Cursor
        Core.cursor = self.cursor = Cursor()
        self.__childrens.append(self.cursor)

        from MainMenu import MainMenu
        self.main_menu = MainMenu()

        from Video import Video
        self.video = Video()
        self.__childrens.append(self.video)

        from Music import Music
        self.music = Music()
        self.__childrens.append(self.music)

        from Tray import Tray
        self.tray = Tray()
        self.__childrens.append(self.tray)
        
        from Fading import Fading
        self.fading = Fading()
        self.__childrens.append(self.fading)
        
        Core.messages.send('Cursor', 'ChangeLoadGroup', 'Dialog')
        from World.Common.DialogLayer import DialogLayer
        self.dialog = DialogLayer()
        self.__childrens.append(self.dialog)
        Core.messages.send('Cursor', 'ChangeLoadGroup', 'Default')
        
        from Author import Author
        self.author = Author()
        self.__childrens.append(self.author)
        

    def __foreach_func(self, obj, func_name, *args, **kwargs):
        if getattr(obj, func_name, None):
            getattr(obj, func_name)(*args, **kwargs)
        if hasattr(obj, 'objects') and obj.objects:
            for o in obj.objects.itervalues():
                self.__foreach_func(o, func_name, *args, **kwargs)


    def begin_unload_location(self, location_name=None):
        for child in self.__childrens:
            self.__foreach_func(child, 'begin_unload_location', location_name)


    def end_unload_location(self, location_name=None):
        for child in self.__childrens:
            self.__foreach_func(child, 'end_unload_location', location_name)
        

    def begin_load_location(self, location_name=None):
        for child in self.__childrens:
            self.__foreach_func(child, 'begin_load_location', location_name)


    def end_load_location(self, location_name=None):
        for child in self.__childrens:
            self.__foreach_func(child, 'end_load_location', location_name)

    
    def begin_save_game(self, params):
        for child in self.__childrens:
            self.__foreach_func(child, 'begin_save_game', params)


    def end_save_game(self, params):
        for child in self.__childrens:
            self.__foreach_func(child, 'end_save_game', params)


    def begin_load_game(self, params):
        for child in self.__childrens:
            self.__foreach_func(child, 'begin_load_game', params)


    def end_load_game(self, params):
        for child in self.__childrens:
            self.__foreach_func(child, 'end_load_game', params)


    def begin_update(self, dt):
        self.timer.update(dt)
        self.music.update(dt)
        self.cursor.update_begin(dt)


    def end_update(self, dt):
        self.tray.update(dt)
        self.dialog.update(dt)
        self.main_menu.update(dt)
        self.cursor.update_end(dt)
        self.video.update(dt)
        self.fading.update(dt)


    def save(self):
        params = {}
        self.begin_save_game(params)
        self.end_save_game(params)
        self.settings.transient_data = params.copy()
        self.settings.save()
