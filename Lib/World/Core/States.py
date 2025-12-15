import Tanita2, weakmethod

class TimerState(Tanita2.State):
    '''
    State with restarting sequence playback after period of time
    '''
    def __init__(self, sequence, period, on_enter=None, 
                 on_update=None, on_exit=None, link=None):
        '''
        Creating state with sequence playback restarted after `period`
        seconds (may be numeric or tuple (from, to) of numerics)
        '''
        self.period = period
        
        if sequence:
            on_enter = self.__new_handler(on_enter, self.__on_enter)
            on_exit  = self.__new_handler(on_exit,  self.__kill_timer)
        Tanita2.State.__init__(self, sequence, on_enter, on_update, on_exit, link)
    
    # Setting attributes
    def __setattr__(self, name, newval):
        if 'on_enter' == name: newval = self.__new_handler(newval, self.__on_enter)
        if 'on_exit' == name: newval = self.__new_handler(newval,  self.__kill_timer)
        Tanita2.State.__setattr__(self, name, newval)

    # Create handler for user function
    def __new_handler(self, user_handler, own_handler):
        if callable(user_handler):
            user_handler = weakmethod.WeakMethod(user_handler)
            return lambda: (own_handler(), user_handler()) and None
        return own_handler
    
    # entering to state
    def __on_enter(self):
        self.__kill_timer()
        self.parent.sequences[self.sequence].stop()
        self.__set_timer()

    # Setting timer on entering to state
    def __set_timer(self):
        import Core

        if isinstance(self.period, (list, tuple)):
            period = Core.random(self.period[0], self.period[1])
        else:
            period = self.period
        Core.timer.append(period, self.__restart_sequence, id(self))
    
    # Restarting sequence on timer
    def __restart_sequence(self):
        seq = self.parent.sequences[self.sequence]
        seq.frame = 0
        seq.play()
        self.__set_timer()
    
    # Killing timer on exit from state
    def __kill_timer(self):
        import Core
        del Core.timer[id(self)]
