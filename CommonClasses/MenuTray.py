try:
    from Core import *
except: pass


class MenuTray:
    '''
    Menu_tray

    '''
    def __init__(self):
        from Additional import Effects
        self.__effects = self.objects['Effects'] = Effects()
        self.__buttons = []
        self.__left_x = vec2(0, 0)
        self.__right_x = vec2(1024, 768)
        self.__width = 0
        self.__name = None
        messages.register('MenuTray', self)
        self.__backup_update = self.update
        self.update = self.waiting_transparent


    def waiting_transparent(self, dt):
        self.__backup_update(dt)
        if engine.fading.is_transparent:
            messages.send('Menu', 'InternalCommand', command='SetButtons', buttons=self)
            self.update = self.__backup_update


    def begin_render(self, dt):
        self.__backup_update(dt)


    def end_render(self, dt):
        for button, size in self.__buttons:
            button.update(0)


    def loadButtons(self, current_buttons, total_buttons):
        buttons = {}

        for obj in self.objects.itervalues():
            if not obj.objects.has_key('Button'):
                continue

            button = obj.objects['Button']
            button.position.x = -2048
            button.state = '__empty__'

            class_name = obj.__class__.__name__

            if class_name in current_buttons:
                i = current_buttons.index(class_name)
                size = total_buttons[class_name]
                buttons[i] = (button, size)

        numbers = list(buttons.iterkeys())
        numbers.sort()

        for i in numbers:
            self.__buttons.append(buttons[i])


    def __refresh(self):
        self.__width = 0
        for button, size in self.__buttons:
            self.__width += size.x
            self.__left_x = button.position.x - button.absolute_position.x
            self.__right_x = self.__left_x + 1024


    def __move(self, direction, appear, callback):
        if direction == 'Left':
            delta = -1
        else:
            delta = +1

        self.__refresh()

        self.__effects.clear()

        button_start = (1024 - self.__width) / 2.0 + self.__left_x

        curr_x = 0

        speed = 0.5
        delay = 0.0
        total = speed

        for i in xrange(len(self.__buttons)):

            button, size = self.__buttons[i]

            if not appear:
                p1 = vec2(button.position)
                p2 = vec2(button.position.x - curr_x - delta * 1024, button.position.y)
            else:
                p1 = vec2(button_start + curr_x + delta * 1024, button.position.y)
                p2 = vec2(button_start + curr_x, button.position.y)
                button.position = vec2(p1)
                button.state = 'Stay'

            curr_x += size.x
            total += delay

            if delta < 0:
                d = speed - delay
            if delta > 0:
                d = delay

            from Additional.Effects import MoveLineEffect
            effect = MoveLineEffect(p1, p2, speed, d)
            self.__effects.append(button, effect)

            if appear:
                from Additional import CallbackEffect
                effect = CallbackEffect(lambda: messages.send('Interface.Buttons.Sounds', 'Play'), speed + d)
                self.__effects.append(self, effect)

            delay += speed / len(self.__buttons)

        from Additional.Effects import CallbackEffect
        effect = CallbackEffect(callback, total)
        self.__effects.append(self, effect)



    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'Move':
            direction = kwargs['direction']
            appear = ('appear' in kwargs and [kwargs['appear']] or [False]).pop()
            callback = ('callback' in kwargs and [kwargs['callback']] or [lambda: None]).pop()
            self.__move(direction, appear, callback)
            return True
