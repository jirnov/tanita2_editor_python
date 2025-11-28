try:
    from Core import *
    import Lib.World.Globals
    from CommonClasses.Overrides.DialogCharacter import DialogCharacter
except: 
    class DialogCharacter: pass

class SoundGags(DialogCharacter):
    '''
    Sound gags container

    '''
    def __init__(self):
        self.__messageReceiver = 'soundgag_%d' % id(self)
        DialogCharacter.__init__(self, self.__messageReceiver)
        
        self.stateEmpty.link = self.__link

        self.is_active = getattr(self, 'is_active', lambda name: True)

        self.__enabledRegions = []
        self.__disabledRegions = []
        
        for name, region in self.objects.iteritems():
            if self.is_active(name):
                self.__enabledRegions.append((name, region))
            else:
                region.previous_cursor = region.cursor
                region.cursor = CURSOR_NORMAL
                self.__disabledRegions.append((name, region))
            region.soundList = [soundname for soundname in self.sounds.iterkeys() if soundname.startswith(name)]
            assert len(region.soundList) > 0
            region.currentSound = 0
            region.allowRandom = False
        for sound in self.sounds.itervalues():
            sound.nonpositionable = True
        
        self._enterDialogState = self._exitDialogState = self._stayInDialog = lambda: None
        
    
    def __link(self):
        # Проверяем выключенные регионы
        for name, region in list(self.__disabledRegions):
            if self.is_active(name):
                self.__disabledRegions.remove((name, region))
                region.cursor = region.previous_cursor
                self.__enabledRegions.append((name, region))

        # Проигрываем первый раз подряд, затем в случайном порядке.
        for name, region in list(self.__enabledRegions):
            if not self.is_active(name):
                self.__enabledRegions.remove((name, region))
                region.previous_cursor = region.cursor
                region.cursor = CURSOR_NORMAL
                self.__disabledRegions.append((name, region))
                continue

            if region.click:
                if region.allowRandom:
                    oldSound = region.currentSound
                    region.currentSound = randint(0, 1000) % len(region.soundList)
                    if oldSound == region.currentSound:
                        region.currentSound = (region.currentSound + 1) % len(region.soundList)
                
                phrase = [(self.__messageReceiver, 'play_sound', region.soundList[region.currentSound])]
                messages.send('Author', 'say', phrase)
                
                if not region.allowRandom:
                    region.currentSound = region.currentSound + 1
                    if region.currentSound >= len(region.soundList):
                        region.allowRandom = True
                break
