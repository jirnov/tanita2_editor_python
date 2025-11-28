from Core import *

class DialogCharacter:
    def __init__(self, messageHandlerName):
        if messages.has_key(messageHandlerName):
            messages.unregister(messageHandlerName)
        messages.register(messageHandlerName, self)
        self.__isTalking = False
        
        if messageHandlerName.endswith('_author'):
            for sound in self.sounds.itervalues():
                sound.nonpositionable = True
            self._enterDialogState = lambda: None
            self._stayInDialog = lambda: None
            self._exitDialogState = lambda: None
        
    
    def loadLipsync(self, lipsyncModule):
        flip = lipsyncModule.flip
        for name, sound, profile, frames in lipsyncModule.animations:
            self.addTalkSequence(name, sound, frames, profile, flip)
        if hasattr(self, 'onLipsyncLoad'):
            self.onLipsyncLoad(flip)
        
    
    def on_message(self, messageid, *args, **kwargs):
        if messageid == 'on_wait_click':
            if not self.__isTalking or not kwargs['click']:
                return
            for sound in self.sounds.itervalues():
                sound.rewind()
            self.__isTalking = False
            return True

        if messageid == 'run_callback':
            callback, callback_params = args
            callback()
            messages.send(*callback_params)
            return True
        
        if messageid == 'switch_sound_state':
            stateName, callback_params = args
            stateName, soundName = stateName
            targetState = self.states[stateName]
            prevOnExit = targetState.on_exit
            
            def onExit():
                self.__isTalking = False
                targetState.on_exit = prevOnExit
                prevOnExit()
                messages.send(*callback_params)
            
            fromAuthor = 'from_author' in kwargs
            
            sound = self.sounds[soundName]
            def link():
                if sound.is_over or not self.__isTalking:
                    targetState.link = lambda: None
                    if fromAuthor:
                        self._exitBusyState()
                    else:
                        self._stayInDialog()
            
            targetState.on_exit = onExit
            targetState.link = link
            self.__isTalking = True
            if fromAuthor:
                self._enterBusyState(stateName)
            else:
                self.state = stateName
            return True
        
        if messageid == 'switch_state':
            stateName, callback_params = args
            targetState = self.states[stateName]
            prevOnExit = targetState.on_exit
            
            def onExit():
                targetState.on_exit = prevOnExit
                prevOnExit()
                messages.send(*callback_params)
            
            sequence = self.sequences[stateName]
            def link():
                if sequence.is_over:
                    targetState.link = lambda: None
                    self._stayInDialog()
            
            targetState.on_exit = onExit
            targetState.link = link
            self.state = stateName
            return True
        
        if messageid == 'move_to':
            if not self.states.has_key('__DialogStay'):
                self.states['__DialogStay'] = State('Stay')
            
            pointName, callback_params = args
            point = getattr(engine.points, pointName)
            
            def callback():
                self._enterDialogState()
                messages.send(*callback_params)
            
            #self._exitDialogState()
            if not self.sendTo(point, callback, '__DialogStay'):
#                print "WARN: unable to send character to target point"
                callback()
            return True
        
        if messageid == 'play_sound':
            soundName, callback_params = args

            if not self.sounds.has_key(soundName):
#                print 'WARNING: sound %s not found!' % repr(soundName)
                messages.send(*callback_params)
                return 

            sound = self.sounds[soundName]
            state = self.states[self.state]
            prevLink = state.link
            
            def link():
                if sound.is_over or not self.__isTalking:
                    self.__isTalking = False
                    state.link = prevLink
                    messages.send(*callback_params)
                    self._stayInDialog()
            
            state.link = link
            self.__isTalking = True
            sound.play()
            return True
