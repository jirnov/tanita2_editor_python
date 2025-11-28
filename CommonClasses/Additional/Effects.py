from Core import vec2, Point
from weakref import ref
from weakmethod import WeakMethod
from Tanita2 import GameObject
from math import hypot, acos, cos, sin, radians, pi


__all__ = [ 'Effects',
            'MoveLineEffect',
            'FrameCallbackEffect',
            'ScaleEffect',
            'RotateEffect',
            'CallbackEffect' ]



class Effect(GameObject):
    '''
    Базовый класс для всех эффектов

    '''
    def __init__(self, speed, delay=0.0):
        '''
        speed - время работы эффекта в секундах
        delay - время в секундах до начала действия эффекта

        '''
        GameObject.__init__(self)
        self.__delay = float(delay)
        self.__is_completed = False
        self.__is_running = False
        self.__params = None
        self.__k = 0.0
        if speed <= 0.0:
            speed = 0.001
        self.__speed = float(speed)


    def is_completed(self):
        return self.__is_completed


    def on_apply_params(self, object):
        pass


    def set_params(self, params):
        self.__params = params


    def get_params(self):
        return self.__params


    def apply_params(self, object):
        if self.__is_running:
            self.on_apply_params(object)


    def update(self, dt):
        if not self.__is_running:
            self.__delay -= dt
            if self.__delay < 0.0:
                self.__is_running = True
        if self.__is_running:
            self.__k += dt / self.__speed
            if self.__k > 1.0:
                self.__k = 1.0
                self.__is_completed = True
                self.update = None
            self.on_update()



    def get_percent(self, source, destination):
        return source * (1.0 - self.__k) + destination * self.__k




class CallbackEffect(Effect):
    '''
    Вызов функции после delay секунд

    '''
    def __init__(self, handler, delay=0.0):
        Effect.__init__(self, speed=delay)
        self.__handler = WeakMethod(handler)


    def on_update(self):
        if self.get_percent(0.0, 1.0) == 1.0:
            if self.__handler:
                self.__handler()



class FrameCallbackEffect(Effect):
    '''
    Вызов функции при каждом обновлении
    Функция имеет вид func(k), где k - промежуток от 0.0 до 1.0

    '''
    def __init__(self, handler, speed, delay=0.0):
        Effect.__init__(self, speed, delay)
        self.__handler = WeakMethod(handler)


    def on_update(self):
        if self.__handler:
            self.__handler(self.get_percent(0.0, 1.0))




class ScaleEffect(Effect):
    '''
    Увеличение объекта одновременно по двух осям

    '''
    def __init__(self, source, destination, speed, delay=0.0):
        Effect.__init__(self, speed, delay)
        self.__source = source
        self.__destination = destination


    def on_update(self):
        self.set_params(vec2(self.get_percent(self.__source, self.__destination)))


    def on_apply_params(self, object):
        object.scale = self.get_params()




class RotateEffect(Effect):
    '''
    Изменение угла поворота объекта, углы в градусах

    '''
    def __init__(self, source, destination, speed, delay=0.0):
        Effect.__init__(self, speed, delay)
        self.__source = source
        self.__destination = destination


    def on_update(self):
        self.set_params(self.get_percent(self.__source, self.__destination))


    def on_apply_params(self, object):
        object.rotation = self.get_params()



class MoveLineEffect(Effect):
    '''
    Движение по прямой

    '''
    def __init__(self, source, destination, speed, delay=0.0):
        Effect.__init__(self, speed, delay)
        self.__source = source
        self.__destination = destination


    def on_update(self):
        self.set_params(vec2(self.get_percent(self.__source, self.__destination)))


    def on_apply_params(self, object):
        object.position = self.get_params()



class MovePathEffect(Effect):
    '''
    Движение по пути

    '''
    def __init__(self, path, speed, delay=0.0):
        '''
        path - tuple, каждый элемент которого представляет собой point и callback

        '''
        Effect.__init__(self, speed, delay)

        self.path = []

        for i in xrange(len(path)):
            if type(path[i]) == tuple:
                self.path.append((path[i][0], path[i][1]))
            else:
                self.path.append((path[i], lambda: None))

        distances = [0.0]
        distance = 0
        for i, j in zip(xrange(0, len(self.path) - 1), xrange(1, len(self.path))):
            p1 = self.path[i][0]
            p2 = self.path[j][0]
            d = hypot(p1.x - p2.x, p1.y - p2.y)
            distance += d
            distances.append(distance)

        self.speeds = []
        for d in distances:
            self.speeds.append(d / distance)
        self.next_index = 1


    def on_update(self):
        p = self.get_percent(0.0, 1.0)
        for i, j in zip(xrange(0, len(self.speeds) - 1), xrange(1, len(self.speeds))):
            if self.speeds[i] <= p < self.speeds[j]:
                percent = (p - self.speeds[i]) / (self.speeds[j] - self.speeds[i])
                if j != self.next_index:
                    self.next_index = j
                    self.path[self.next_index - 1][1]()
                p1 = self.path[self.next_index - 1][0]
                p2 = self.path[self.next_index][0]
                self.set_params(p1 * (1.0 - percent) + p2 * percent)
                break


    def on_apply_params(self, object):
        object.position = self.get_params()




class Holder(GameObject):
    def __init__(self, object):
        GameObject.__init__(self)
        self.__object = ref(object)


    def append(self, effect):
        # Ищем завершенный эффект
        found = None
        for key, obj in self.objects.iteritems():
            if obj.is_completed():
                found = key
                break
        # Если есть завершенный эффект, заменяем его на новый
        # иначе добавляем новый в конец очереди
        if found:
            self.objects[found] = effect
        else:
            self.objects[str(len(self.objects))] = effect


    def update(self, dt):
        GameObject.update(self, dt)
        complete = True
        object = self.__object()
        if object:
            for effect in self.objects.itervalues():
                effect.apply_params(object)
                complete &= effect.is_completed()
        if complete:
            for key, holder in self.parent.objects.iteritems():
                if holder == self:
                    del self.parent.objects[key]
                    return


    def forceUnload(self):
        self.__object = None
        GameObject.forceUnload(self)




class Effects(GameObject):
    def clear(self):
        self.objects.clear()


    def is_empty(self):
        return len(self.objects) == 0


    def append(self, object, effect):
        '''
        Добавление эффекта к объекту

        '''
        key = self.gen_key(object)
        if not self.objects.has_key(key):
            self.objects[key] = Holder(object)
        self.objects[key].append(effect)


    def gen_key(self, object):
        '''
        Генератор уникального ключа для объекта

        '''
        return str(id(object))


    def pause(self):
        self.update = lambda dt: None


    def resume(self):
        self.update = lambda dt: GameObject.update(self, dt)


    def remove(self, object):
        '''
        Удаление эффектов у объекта

        '''
        if self.has_key(object):
            key = self.gen_key(object)
            del self.objects[key]


    def has_key(self, object):
        return self.objects.has_key(self.gen_key(object))
