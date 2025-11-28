from Tanita2 import GameObject
from Core import messages, timer, engine

class Author(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        messages.register('Author', self, 'Environment')
        self.__isTalking = False
        self.__setTalking(False)


    def on_message(self, msgid, *args, **kwargs):
        if msgid == 'say' and not self.__isTalking:
            self.__setTalking(True)
            self.__say(*args, **kwargs)
            return True

        if msgid == 'short_say':
            self.__short_say(*args, **kwargs)
            return True
        
        if msgid == 'callback':
            nextStates = args[0]
            
            if nextStates != []:
                timer.append(0, lambda: self.__startAction(nextStates))
            else:
                messages.send('Cursor', 'WaitEnable', False)
                self.__setTalking(False)
            return True


    def __setTalking(self, flag):
        self.__isTalking = flag
        engine.autor.is_talking = flag


    def __waitFading(self, phrases):
        if engine.fading.is_transparent:
            self.__say(phrases)
        else:
            timer.append(0, lambda: self.__waitFading(phrases))
        


    def __say(self, phrases, waitFading=False):
        messages.send('Cursor', 'WaitEnable', True)
        if waitFading:
            self.__waitFading(phrases)
        else:
            self.__startAction(phrases)


    def __short_say(self, soundName, waitFading=False, callback=None):
        autorName = '%s_author' % engine.current_location.name.lower()
        phrases = [(autorName, 'play_sound', soundName)]
        if callback:
            phrases.append((autorName, 'run_callback', callback))
        messages.send('Author', 'say', phrases, waitFading)
        
    
    def __startAction(self, actionSequence):
        target, name, state = actionSequence[0]
        messages.send(target, name, state, ('Author', 'callback', actionSequence[1:]), from_author=True)
        


    def begin_unload_location(self, location_name=None):
        self.__setTalking(False)
