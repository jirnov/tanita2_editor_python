try:
    from Core import *
except: pass

class Dialog:
    '''
    Dialog options
    
    '''
    
    def __init__(self):
        import Core
        for obj in self.objects.itervalues():
            Core.environment.dialog.add_option(obj)
        self.begin_update()
        self.end_update()
        self.objects.clear()
        