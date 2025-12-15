from Tanita2 import vec2

#[
#    ('wait', 3),
#    ('click', (640, 480)),
#    ('wait', 3),
#    ('condition', 'engine.fading.is_transparent', 2),
#]
class Unitest:
    def __init__(self, commands):
        self.__cursor_position = vec2(-1024, -1024)
        self.__cursor_timer = None
        self.__cursor_buttons = None

        self.__keycode = None
        self.__keypress_timer = None

        self.__current = 0
        self.__is_waiting = False
        self.__is_waiting_cursor = False
        self.__timer = 0
        self.__commands = list(commands)


    def update(self, dt):
        import Lib.Globals
        Lib.Globals.cursor_position = vec2(self.__cursor_position)

        if self.check_keypress():
            return

        if self.check_click():
            return

        if self.__is_waiting:
            self.__timer -= dt
            if self.__timer > 0:
                return
            self.__is_waiting = False

        command = self.__commands[self.__current]

        tag = type(command) == str and command or command[0]

        if hasattr(self, tag):
            print 'Run command %s' % repr(tag)
            if type(command) == str:
                getattr(self, tag)()
            else:
                getattr(self, tag)(*command[1:])
        else:
            print 'Unknown unitest command %s' % repr(tag)


    def check_keypress(self):
        if self.__keycode is None:
            return

        from Core import engine
        if not engine.keyboard.is_enabled:
            return True
        if self.__keypress_timer > 0:
            self.__keypress_timer -= 1
            return True
        from Core import messages
        messages.send_all('on_keypress', keycode=self.__keycode)
        self.__keycode = None
        return True


    def check_click(self):
        if self.__cursor_buttons is None:
            return

        if self.__cursor_timer > 0:
            self.__cursor_timer -= 1
            return True
        import Lib.Globals
        Lib.Globals.mouse_buttons = self.__cursor_buttons
        self.__cursor_buttons = None
        self.__is_waiting = True
        return True


    def exit(self):
        self.update = lambda dt: None


    def wait(self, timer):
        self.__is_waiting = True
        self.__timer = timer
        self.__current += 1


    def keypress(self, keycode=None):
        if keycode is None:
            keycode = 32
        self.__keypress_timer = 2
        self.__keycode = keycode
        self.__current += 1
        

    def click(self, x=None, y=None):
        self.__cursor_buttons = 0x01
        self.__cursor_timer = 2
        if not x is None and not y is None:
            import Lib.Globals
            Lib.Globals.cursor_position = vec2(x, y)
            self.__cursor_position = vec2(x, y)
        self.__current += 1


    def condition(self, condition, d):
        from Core import triggers, engine
        if eval(condition):
            self.__current += d


    def goto(self, d):
        self.__current = d
