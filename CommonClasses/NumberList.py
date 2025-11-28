try:
    from Core import *
except: pass

class NumberList:
    '''
    Number List

    '''
    def __init__(self):
        self.__numbers = {}
        for obj in self.objects.itervalues():
            obj.state = '__empty__'
        self.setNumbers(0)
        self.states[self.state].link = self.link


    def link(self):
        for index, number in self.__numbers.iteritems():
            if number.state == 'Stay':
                if number.regClick.over:
                    number.state = 'Over'
                continue
            if number.state == 'Over':
                if number.regClick.exit:
                    number.state = 'Stay'
                    continue
                if number.regClick.click:
                    self.activateNumber(index)
                    continue
            
            
    def setNumbers(self, count, with_activate=True):
        self.__numbers.clear()
        for key, obj in self.objects.iteritems():
            index = int(key[len('N_'):])
            if index < count + 1:
                self.__numbers[index] = obj
                obj.regClick.cursor = CURSOR_ACTIVE
                obj.state = 'Stay'
            else:
                obj.regClick.cursor = CURSOR_NORMAL
                obj.state = '__empty__'
        if with_activate and len(self.__numbers):
            self.activateNumber(1)


    def activateNumber(self, index, with_push=True):
        active = self.__numbers[index]
        active.state = 'Push'
        active.regClick.cursor = CURSOR_NORMAL
        for number in self.__numbers.itervalues():
            if number == active:
                continue
            number.state = 'Stay'
            number.regClick.cursor = CURSOR_ACTIVE
        if with_push and hasattr(self, 'on_push'):
            self.on_push(index)
