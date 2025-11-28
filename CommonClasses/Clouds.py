try:
    import Tanita2
    from Tanita2 import *
except: pass

class Clouds(Tanita2.GameObject):
    '''
    Clouds container
    '''
    def __init__(self):
        from Core import timer
        timer.append(0, self.initialize)



    def initialize(self):
        from Core import engine, random
        self.left_x = None
        self.right_x = None
        from Additional import Effects
        self.effects = self.objects['Effects'] = Effects()
        for name, cloud in self.objects.iteritems():
            speed = engine.current_location.width / 25.0 * random(0.95, 1.05)
            if name.startswith('Big_'):
                speed /= 1.5
            elif name.startswith('Small_'):
                speed /= 0.5
            self.__move(cloud, speed, initialize=True)


    def __move(self, obj, speed, initialize=False):
        if self.left_x is None:
            self.left_x = -self.position.x - 256
        if self.right_x is None:
            from Core import engine
            self.right_x = self.left_x + engine.current_location.width + 256

        self.effects.remove(obj)
        correct_speed = speed

        if initialize:
            x = obj.position.x
            correct_speed = speed * (self.right_x - obj.position.x) / (self.right_x - self.left_x)
        else:
            x = self.left_x

        from Additional import MoveLineEffect
        effect = MoveLineEffect(vec2(x, obj.position.y), vec2(self.right_x, obj.position.y), correct_speed)
        self.effects.append(obj, effect)
        from Additional import CallbackEffect
        effect = CallbackEffect(lambda: self.__move(obj, speed), correct_speed + 0.25)
        self.effects.append(obj, effect)
