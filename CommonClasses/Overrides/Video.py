from Tanita2 import AnimatedObject, State, ResourceId, ResourceType
from Core import vec2, engine, messages
'''
Video player

'''

class Video(AnimatedObject):
    def __init__(self):
        AnimatedObject.__init__(self)
        self.video = self.objects['Video'] = AnimatedObject()
        self.video.scale = vec2(1024.0 / 640, 768.0 / 480)
        self.video.stateEmpty = self.video.states['__empty__'] = State(None)
        self.video.state = '__empty__'
        self.stateStay = self.states['Stay'] = State(None)
        self.statePlay = self.states['Play'] = State(None)
        self.state = 'Stay'
        self.is_visible = False
        self.is_hidden = True
        self.enable_menu = False
        messages.register('Video', self, 'Environment')


    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'Play':
            self.play(*args, **kwargs)
            return True
        if msg_id == 'on_click':
            if engine.keyboard.is_enabled and self.is_visible:
                self.state = 'Stay'
                return True
        if msg_id == 'on_wait_click':
            if engine.keyboard.is_enabled and self.is_visible:
                self.state = 'Stay'
                return True
        if msg_id == 'on_keypress':
            if self.is_visible:
                self.state = 'Stay'
                return True


    def play(self, path, callback, disable_back=True):
        if not self.is_hidden:
            return

        def play_on_enter():
            self.is_visible = True
            engine.video.is_playing = True
            self.video.sequences['Video'].play()

        def play_link():
            if self.video.sequences['Video'].is_playing:
                return
            return 'Stay'

        def video_callback():
            self.video.sequences['Video'].stop()
            del self.video.sequences['Video']
            self.video.stateEmpty.sequence = None
            self.is_hidden = True
            engine.video.is_playing = False
            engine.keyboard.is_enabled = True
            messages.send('Music', 'Play')
            if disable_back:
                messages.send('Location', 'Enable')
                if self.enable_menu:
                    messages.send('Menu', 'Enable')
            self.enable_menu = False
            if callback:
                callback()

        def play_on_exit():
            self.is_visible = False
            engine.keyboard.is_enabled = False
            messages.send('Fading', 'doOpaque', callback=video_callback)


        def transparent_callback():
            self.is_visible = True
            engine.keyboard.is_enabled = True

        def opaque_callback():
            self.video.add_video_sound_sequence('Video', ResourceId(path, ResourceType.RESOURCE_TYPE_OGG))
            self.video.stateEmpty.sequence = 'Video'
            self.statePlay.on_enter = play_on_enter
            self.statePlay.link = play_link
            self.statePlay.on_exit = play_on_exit
            self.state = 'Play'
            messages.send('Music', 'Stop')

            self.enable_menu = False
            if disable_back:
                messages.send('Location', 'Disable')
                if engine.menu.is_enabled:
                    messages.send('Menu', 'Disable')
                    self.enable_menu = True

            messages.send('Fading', 'doTransparent', callback=transparent_callback)

        self.is_hidden = False
        engine.keyboard.is_enabled = False

        if engine.fading.is_opaque:
            opaque_callback()
        else:
            messages.send('Fading', 'doOpaque', callback=opaque_callback)
