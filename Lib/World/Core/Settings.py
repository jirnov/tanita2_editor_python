'''
Save and load global settings.

'''
import os, os.path

class Settings:
    def __init__(self):
        import Lib
        filename = 'Saves\\settings.sav'
        if not Lib.config['use_saves_dir']:
            appdata = os.environ['APPDATA']
            dirname = os.path.join(appdata, 'Смешарики - Параллельные миры')
            if not os.path.isdir(dirname):
                os.mkdir(dirname)
            filename = os.path.join(dirname, 'settings.sav')
        print 'Using file "%s" for saves' %  filename
        self.__dict__['file'] = filename
        self.__dict__['loaded'] = False
        self.__dict__['params'] = \
        {
            'transient_data' : {},
            'cleared_data' : {},
            'steady_data' : { 'music_volume' : 91, 'sound_volume' : 77 },
            'save_data' : [],
        }
        self.load()
        self.save()


    def __getattr__(self, name):
        if not self.loaded:
            self.load()
        if self.params.has_key(name):
            return self.params[name]
        raise AttributeError, name


    def __setattr__(self, name, value):
        if self.params.has_key(name):
            self.params[name] = value
        else:
            raise AttributeError, name


    def load(self):
        self.__dict__['loaded'] = True
        try:
            import cPickle, gzip
            params = cPickle.loads(open(self.__dict__['file'], 'rb').read())
            for key in self.params.iterkeys():
                self.params[key] = params[key]
        except:
            print 'Can`t load file "%s"' % self.__dict__['file']


    def save(self):
        try:
            import cPickle, gzip
            open(self.__dict__['file'], 'wb', 9).write(cPickle.dumps(self.params, 1))
        except:
            print 'Can`t save file "%s"' % self.__dict__['file']
