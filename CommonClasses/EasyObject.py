try:
    from Core import *
    import Lib.World.Globals
except: pass

class EasyObject:
    '''
    Easy object

    '''
    def __init__(self):
        pass

    # Set expression for state
    # example:
    # append_condition('Stay', 'Move', ['regOver', 'over'])
    # append_condition('Move', 'Stay', ['seqMove', 'is_over'])
    # append_condition('Stay', 'Move', ['timer', 3, 5])
    # append_condition('Stay', 'Move', ['timer', 4])

    def append_condition(self, state, next_state, condition):
        assert len(condition) > 1, "Too little conditions"
        if condition[0].lower() == 'message':
            assert len(condition) < 3, "Too many conditions"
            def link():
                if messages.recv(condition[1]):
                    return next_state
            self.states[state].link = link
            return
        if condition[0].lower() == 'timer':
            assert len(condition) < 4, "Too many conditions"
            def timer_handler():
                self.state = next_state
            def on_enter():
                if len(condition) == 3:
                    timer.append(randint(condition[1], condition[2]), timer_handler)
                else:
                    timer.append(condition[1], timer_handler)
            self.states[state].on_enter = on_enter
            return
        def link():
            attr = self
            for i in range(0, len(condition)):
                attr = getattr(attr, condition[i])
            if attr:
                return next_state
        self.states[state].link = link
