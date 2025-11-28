try:
    from Core import *
    import Lib.World.Globals
except: pass

class TrayItem:
    '''
    Takeable item

    '''
    def __init__(self):
        self.stateDisabled = self.states['Disabled'] = State(None)
        self.stateEmpty.on_enter = self.empty_on_enter
        self.stateDisabled.on_enter = self.empty_on_enter
        self.stateStay.link = self.stay_link
        self.may_be_taken = getattr(self, 'may_be_taken', lambda: True)
        self.state = 'Stay'


    def empty_on_enter(self):
        self.regTake.cursor = CURSOR_NORMAL


    def stay_link(self):
        if self.may_be_taken():
            if self.regTake.cursor == CURSOR_NORMAL:
                self.regTake.cursor = CURSOR_TAKE
            if self.regTake.click:
                from Core import messages
                messages.send('Tray', 'Show')
                messages.send('Tray', 'Push', name=self.name[len('Item_'):])
                # Deactivating block regions
                for r in self.objects.itervalues():
                    if isinstance(r, BlockRegion): 
                        r.disable()
                return 'Disabled'
        elif self.regTake.cursor == CURSOR_TAKE:
            self.regTake.cursor = CURSOR_NORMAL
