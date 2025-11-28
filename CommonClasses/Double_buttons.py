try:
    from Core import *
except:
    pass


class Double_buttons:
    '''
    Multiple Button

    '''
    def __init__(self):
        self.__buttons = []
        self.__next_states = []
        for obj in self.objects.itervalues():
            self.append(obj)
        self.__default_states = ['__empty__', 'Stay', 'Over', 'Push']
        self.stateStay = self.states['Stay'] = State(None)
        self.statePush = self.states['Push'] = State(None)
        self.stateOver = self.states['Over'] = State(None)
        self.stateWait = self.states['Wait'] = State(None)
        self.stateFreeze = self.states['Freeze'] = State(None)

        self.stateStay.on_enter = lambda: self.change_button_states('Stay')
        self.stateStay.link = self.stay_link
        self.statePush.on_enter = lambda: self.change_button_states('Push')
        self.statePush.link = self.push_link
        self.stateOver.on_enter = lambda: self.change_button_states('Over')
        self.stateOver.link = self.over_link
        self.stateWait.on_enter = lambda: self.change_button_states('Wait')
        self.stateFreeze.link = self.freeze_link
        self.state = 'Stay'


    def __on_push(self):
        if hasattr(self, 'on_push'):
            self.on_push()


    def __is_over(self, seq):
        if seq.reversed:
            return seq.frame == 0
        return seq.frame == seq.frame_count - 1


    def clear(self):
        self.__buttons = []


    def remove(self, button):
        unused_next_states = []
        for button_tuple in self.__next_states:
            if button_tuple[0] == button:
                unused_next_states.append(button_tuple)
        for button_tuple in unused_next_states:
            self.__next_states.remove(button_tuple)
        self.__buttons.remove(button)


    def append(self, button):
        if button.states.has_key('Stay'):
            button.state = 'Stay'
        self.__buttons.append(button)


    def change_button_states(self, next_state, force=False):
        for button in self.__buttons:
            if force:
                button.state = next_state
            else:
                self.__next_states.append((button, next_state))


    def update_states(self):
        if not len(self.__next_states):
            return
        removed = []
        for button, next_state in self.__next_states:
            if not button.states.has_key(next_state):
                removed.append((button, next_state))
                continue
            if not button.sequences.has_key(button.state):
                button.state = next_state
                removed.append((button, next_state))
                continue
            if button.state == next_state:
                removed.append((button, next_state))
                continue
            if self.__is_over(button.sequences[button.state]):
                button.state = next_state
                removed.append((button, next_state))
                continue
        for button_state in removed:
            self.__next_states.remove(button_state)


    def stay_link(self):
        self.update_states()
        for button in self.__buttons:
            if button.regClick.enter:
                return 'Over'


    def over_link(self):
        self.update_states()
        for button in self.__buttons:
            if button.regClick.exit:
                return 'Stay'
            if button.regClick.click:
                return 'Push'


    def push_link(self):
        self.update_states()
        for button in self.__buttons:
            if button.state not in self.__default_states:
                continue
            if button.state == self.state:
                if button.sequences[self.state].is_over:
                    next_state = 'Stay'
                    for button in self.__buttons:
                        if button.states.has_key('Freeze'):
                            next_state = 'Freeze'
                        elif button.states.has_key('Wait'):
                            self.stateWait.link = self.wait_link
                            next_state = 'Wait'
                        else:
                            button.state = 'Stay'
                    if next_state != 'Wait':
                        self.__on_push()
                    return next_state


    def wait_link(self):
        self.update_states()
        for button in self.__buttons:
            if button.state == 'Wait':
                self.__on_push()
                self.stateWait.link = None


    def freeze_link(self):
        self.update_states()
        is_over = True
        for button in self.__buttons:
            if button.state != 'Stay':
                is_over = False
        if is_over:
            return 'Stay'
