try:
    from Core import *
except: pass

class Button:
    '''
    Button

    '''
    def __init__(self):
        if not self.states.has_key('Push'):
            self.seqPush = self.sequences['Push'] = self.sequences['Over']
            self.statePush = self.states['Push'] = State('Over')
        if self.sequences.has_key('Disable'):
            self.stateEmpty.sequence = 'Disable'
        self.stateOver.link = self.over_link
        self.stateStay.on_enter = self.stay_on_enter
        self.stateStay.link = self.stay_link
        self.statePush.link = self.push_link
        self.stateEmpty.on_enter = self.empty_on_enter
        self.backup_cursor = self.regClick.cursor


    def empty_on_enter(self):
        if self.backup_cursor is None:
            self.backup_cursor = self.regClick.cursor
        self.regClick.cursor = CURSOR_NORMAL


    def stay_on_enter(self):
        if self.backup_cursor:
            self.regClick.cursor = self.backup_cursor
            self.backup_cursor = None


    def stay_link(self):
        if self.regClick.over:
            return 'Over'


    def over_link(self):
        if self.regClick.click:
            return 'Push'
        if not self.regClick.over:
            return 'Stay'


    def push_link(self):
        if self.seqPush.is_over:
            state = self.state
            if hasattr(self, 'on_push'):
                self.on_push()
            if state == self.state:
                return 'Stay'
