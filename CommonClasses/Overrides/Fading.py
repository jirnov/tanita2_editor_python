from Tanita2 import GameObject
from Core import messages
'''
Fading effects

'''
class Fading(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        from World.Common.FadingLayer.FadingPackage import Fading
        self.fading = self.objects['Fading'] = Fading()
        messages.register('Fading', self, 'Environment')


    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'Opaque':
            self.fading.doOpaque(force=True, callback=self.__get_callback(kwargs))
            return True

        if msg_id == 'Transparent':
            self.fading.doTransparent(force=True, callback=self.__get_callback(kwargs))
            return True

        if msg_id == 'doOpaque':
            self.fading.doOpaque(delay=self.__get_delay(kwargs), callback=self.__get_callback(kwargs), with_sound=self.__get_with_sound(kwargs))
            return True

        if msg_id == 'doTransparent':
            self.fading.doTransparent(delay=self.__get_delay(kwargs), callback=self.__get_callback(kwargs))
            return True


    def __get_with_sound(self, kwargs):
        if 'with_sound' in kwargs:
            return kwargs['with_sound']
        return None


    def __get_callback(self, kwargs):
        if 'callback' in kwargs:
            return kwargs['callback']
        return None


    def __get_delay(self, kwargs):
        if 'delay' in kwargs:
            return kwargs['delay']
        return 0.0


    def update(self, dt):
        if dt > 0.1:
            dt = 0.1
        GameObject.update(self, dt)
