try:
    from Core import *
    import Lib.World.Globals
except: pass

class BonusItem:
    '''
    Bonus item

    '''
    def __init__(self):
        self.stateMove.link = self.move_link
        self.stateStay.link = self.stay_link
        self.state = 'Stay'

    def stay_link(self):
        if self.regClick.click:
            self.regClick.cursor = CURSOR_NORMAL
            return 'Move'

    def move_link(self):
        if self.seqMove.is_over:
            import Core
            Core.tray.take_bonus(self.name[len('Bonus_'):])
            del self.parent.objects[self.name]
