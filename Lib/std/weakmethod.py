# File weakmethod.py
from weakref import ref

class WeakMethod:
    """
    Wraps a function or, more importantly, a bound method, in
    a way that allows a bound method's object to be GC'd, while
    providing the same interface as a normal weak reference.
    """

    def __init__(self, fn):
        if hasattr(fn, 'im_self'):
            self.__obj = ref(fn.im_self)
            self.__meth = fn.im_func
            
        else:
            # It's not a bound method.
            self.__obj = None
            self.__meth = fn
    
    def __call__(self, *args, **kws):
        if self.__obj is not None:
            if self.__obj() is None:
                return None
            return self.__meth(self.__obj(), *args, **kws)
        
        else:
            if self.__meth is None:
                return None
            return self.__meth(*args, **kws)
    
    def __getattr__(self, attr):
        if not self.__obj:
            return getattr(self.__meth, attr)
        else:
            if attr == 'im_self':
                return self.__obj()
            if attr == 'im_func':
                return self.__meth
            raise AttributeError, attr
