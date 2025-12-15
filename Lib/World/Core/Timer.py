from weakmethod import WeakMethod

class Timer:
    '''
    Timer class. Allows to append new timer event and remove it by id.
    '''
    def __init__(self):
        self.reset()

    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'Pause':
            self.update = lambda dt: None
            return True
        if msg_id == 'Resume':
            self.update = self.on_update
            return True
    
    def reset(self):
        self.__timers = []
        self.__pending_timers = []
        self.__updating = False
        self.update = self.on_update
        from Core import messages
        if not messages.has_key('Timer', 'Environment'):
            messages.register('Timer', self, 'Environment')

    def end_unload_location(self, location_name=None):
        self.reset()
    
    def append(self, period, handler, id=None):
        '''
        Add new timer event. User function handler will be
        triggered after 'period' seconds.
        
        'id' is an optional identifier of any type for
        subsequent removing by del operator.
        '''
        assert 0 <= period and handler, 'Invalid timer parameters'
        descr = [period, WeakMethod(handler), id]
        (self.__updating and [self.__pending_timers] or [self.__timers])[0].append(descr)
    
    def __delitem__(self, id):
        assert id, 'Timer id is None'
        for i in xrange(len(self.__timers)):
            if self.__timers[i][2] == id:
                del self.__timers[i]
                return

    def has_key(self, id):
        for i in xrange(len(self.__timers)):
            if self.__timers[i][2] == id:
                return True
        return False

    def on_update(self, dt):
        self.__pending_timers = []
        self.__updating = True
        
        # Adding timers
        for timer in self.__timers[:]:
            timer[0] -= dt
            if timer[0] <= 0:
                timer_func = timer[1]
                if timer_func: timer_func()
                continue
            self.__pending_timers.append(timer)
        self.__timers = self.__pending_timers
        self.__updating = False
