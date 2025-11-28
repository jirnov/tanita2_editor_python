from Tanita2 import GameObject, AnimatedObject, State, set_music_volume
from Core import messages, settings

'''
Collection of tracks for current level/menu

'''
class Disk(AnimatedObject):
    def __init__(self):
        AnimatedObject.__init__(self)
        # Скорость включения звука
        self.__speed_up = 25
        # Скорость выключения звука
        self.__speed_down = 50
        # Режим паузы
        self.statePause = self.states['Pause'] = State(None)
        # Режим проигрывания
        self.statePlay = self.states['Play'] = State(None)
        # Режим остановки
        self.stateDo_pause = self.states['Do_pause'] = State(None)
        # Режим начала проигрывания
        self.stateDo_resume = self.states['Do_resume'] = State(None)
        # Доступные треки
        self.__tracks = []
        # Максимальная громкость каждого звука
        self.__volume_max = 90
        # Индекс текущего трека
        self.__index = 0
        # Callback, который вызывается при наступлении паузы
        self.__callback = lambda: None

        self.statePause.on_enter = self.__pause_on_enter
        self.statePlay.link = self.__play_link
        self.stateDo_pause.on_enter = self.__do_pause_on_enter
        self.stateDo_pause.on_update = self.__do_pause_on_update
        self.stateDo_resume.on_enter = self.__do_resume_on_enter
        self.stateDo_resume.on_update = self.__do_resume_on_update

        self.state = 'Pause'


    def __pause_on_enter(self):
        for snd in self.__tracks:
            snd.stop()
        self.__callback()
        self.__callback = lambda: None


    def __play_link(self):
        if self.__tracks[self.__index].is_playing:
            return

        if len(self.__tracks) == 1:
            # Не используем плавное включение звука, если один трек
            self.__tracks[self.__index].play()
            return

        self.__index += 1
        if self.__index > len(self.__tracks) - 1:
            self.__index = 0

        self.__tracks[self.__index].volume = 0
        return 'Do_resume'


    def __do_pause_on_enter(self):
        self.__do_pause_volume = float(self.__tracks[self.__index].volume)


    def __do_pause_on_update(self, dt):
        volume = self.__do_pause_volume
        volume -= dt * self.__speed_down
        if volume > 0:
            self.__tracks[self.__index].volume = int(volume)
            self.__do_pause_volume = volume
            return
        self.__tracks[self.__index].volume = 0
        self.state = 'Pause'


    def __do_resume_on_enter(self):
        self.__do_resume_volume = float(self.__tracks[self.__index].volume)
        self.__tracks[self.__index].volume = 0
        self.__tracks[self.__index].play()


    def __do_resume_on_update(self, dt):
        volume = self.__do_resume_volume
        volume += dt * self.__speed_up
        if volume < self.__volume_max:
            self.__tracks[self.__index].volume = int(volume)
            self.__do_resume_volume = volume
            return
        self.__tracks[self.__index].volume = self.__volume_max
        self.state = 'Play'


    def add_track(self, path):
        from Tanita2 import ResourceId, ResourceType
        self.add_music('%d' % len(self.__tracks), ResourceId(path, ResourceType.RESOURCE_TYPE_OGG))

        snd = self.sounds['%d' % len(self.__tracks)]
        snd.volume = 0
        snd.prolonged = True
        snd.looped = False
        snd.pan = 0
        snd.group = 1
        snd.nonpositionable = True

        self.__tracks.append(snd)


    def pause(self, callback=None):
        callback = (callback is None and [lambda: None] or [callback]).pop()

        if self.state == 'Pause':
            callback()
        else:
            self.__callback = callback
            self.state = 'Do_pause'


    def rewind(self):
        for snd in self.sounds.itervalues():
            snd.rewind()
            snd.stop()


    def is_playing(self):
        return self.state not in ('Pause', 'Do_pause')


    def resume(self):
        self.__callback = lambda: None
        if self.state not in ('Do_resume', 'Play'):
            self.state = 'Do_resume'




class Music(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        self.menu_disk = self.objects['Menu'] = Disk()
        self.game_disk = self.objects['Game'] = Disk()
        self.about_disk = self.objects['About'] = Disk()

        self.menu_disk.add_track('Music/menu.ogg')

        self.about_disk.add_track('Music/about.ogg')

        indexes = list(xrange(0, 5))

        while len(indexes):
            from random import choice
            index = choice(indexes)
            self.game_disk.add_track('Music/song%d.ogg' % index)
            indexes.remove(index)

        import Lib
        if Lib.config.has_key('use_startup_location') and Lib.config['use_startup_location']:
            self.active_disk = self.game_disk
        else:
            self.active_disk = self.menu_disk

        self.active_disk.resume()

        messages.register('Music', self, 'Environment')



    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'Play':
            return self.play()
        if msg_id == 'Stop':
            return self.stop()
        if msg_id == 'ChangeVolume':
            return self.change_volume(*args, **kwargs)
        if msg_id == 'ChangeDisk':
            return self.change_disk(*args, **kwargs)



    def update(self, dt):
        GameObject.update(self, dt)
        if dt > 1:
            # Восстанавливаем громкость
            self.change_volume(int(settings.steady_data['music_volume']))
            from Tanita2 import set_sound_volume, set_video_volume
            set_sound_volume(int(settings.steady_data['sound_volume']))
            set_video_volume(int(settings.steady_data['sound_volume']))


    def change_volume(self, volume):
        from Tanita2 import set_music_volume
        set_music_volume(int(volume))
        return True


    def change_disk(self, disk):
        if self.active_disk == self.objects[disk]:
            return
        disks = { 'Game' : self.game_disk, 'Menu' : self.menu_disk, 'About' : self.about_disk }
        second_disk = self.active_disk
        self.active_disk = disks[disk]
        callback = (second_disk.is_playing() and [self.active_disk.resume] or [lambda: None]).pop()
        self.active_disk.rewind()
        second_disk.pause(callback)
        return True


    def stop(self):
        self.active_disk.pause()
        return True


    def play(self):
        self.active_disk.resume()
        return True
