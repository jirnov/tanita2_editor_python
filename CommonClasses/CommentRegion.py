try:
    from Core import *
    import Lib.World.Globals
except: pass

class CommentRegion:
    '''
    Comment region

    '''
    def __init__(self):        
        self.states[self.state].link = self.link                
        self.__is_active = False
        self.on_click = getattr(self, 'on_click', None)
        self.is_active = getattr(self, 'is_active', lambda: True)
        self.active_cursor = getattr(self, 'active_cursor', lambda:[CURSOR_ACTIVE])

    def link(self):                
        active = self.is_active()
        if active != self.__is_active:            
            self.__is_active = active
            self.regClick.cursor = (active and self.active_cursor() or [CURSOR_NORMAL])[0]
                
        if active:            
            if self.regClick.click and self.on_click:               
                self.on_click()
                
    def on_click(self):        
        import Core
        if Core.active_character:            
            from Core import active_character, engine
            if engine.current_location.name == 'Location09':
                active_character.talk('Stay')
            else:
                active_character.talk('Comment_%s'%self.name.lower())
        
        