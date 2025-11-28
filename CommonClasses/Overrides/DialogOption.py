from Core import *

class DialogOption:
    def __init__(self, messageHandlerName):
        self.__is_ended = False
        self.__messageHandlerName = messageHandlerName
        messages.register(messageHandlerName, self)
        self.__name = messageHandlerName
        
    def on_message(self, msgid, *args, **kwargs):
        if msgid == 'on_exit':
            nextStates = args[0]
            
            if nextStates != []:
                # Продолжаем выполнять цепочку команд.
                timer.append(0.001, lambda: self.start_action(nextStates))
            else:
                # Цепочка команд закончена.
                self.__is_ended = True
            return True
    
    def start_action(self, actionSequence):
        self.__is_ended = False
        target, name, state = actionSequence[0]
        messages.send(target, name, state, (self.__messageHandlerName, 'on_exit', actionSequence[1:]))
    
    def is_action_ended(self):
        return self.__is_ended
        
    def on_action_ended(self):
        pass
    
    def setup_flag(self):
        location, tmp, name = self.__name.rsplit('_', 2)
        setattr(getattr(getattr(triggers, location).dialog, name), 'was_played', True)
