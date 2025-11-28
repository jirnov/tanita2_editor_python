from Tanita2 import GameObject, AnimatedObject, State, vec2
'''
Game cursor

'''
class Cursor(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        from World.Common.CursorsLayer.CursorsPackage import Cursors
        self.cursor = self.objects['Cursor'] = Cursors()
        self.cursor.position = vec2(8, 8)

        self.holder = self.objects['Holder'] = AnimatedObject()
        self.holder.position = self.cursor.position + vec2(16, 16)
        self.holder.states['__empty__'] = State(None)
        self.holder.state = '__empty__'

        self.detach_callback = None
        self.sequence_name = None

        from Core import messages
        messages.register('Cursor', self, 'Environment')


    def on_message(self, msg_id, *args, **kwargs):
        if msg_id == 'ClearGroup':
            self.clear_group(*args, **kwargs)
            return True
        if msg_id == 'ChangeLoadGroup':
            self.change_load_group(*args, **kwargs)
            return True
        if msg_id == 'EnableGroups':
            self.enable_groups(*args, **kwargs)
            return True
        if msg_id == 'DisableGroups':
            self.disable_groups(*args, **kwargs)
            return True
        if msg_id == 'BackupGroups':
            self.backup_groups(*args, **kwargs)
            return True
        if msg_id == 'RestoreGroups':
            self.restore_groups(*args, **kwargs)
            return True
        if msg_id == 'Disable':
            self.disable()
            return True
        if msg_id == 'Enable':
            self.enable()
            return True
        if msg_id == 'Append':
            self.append(*args, **kwargs)
            return True
        if msg_id == 'Remove':
            self.remove(*args, **kwargs)
            return True
        if msg_id == 'AttachSequence':
            self.attach_sequence(*args, **kwargs)
            return True
        if msg_id == 'DetachSequence':
            self.detach_sequence()
            return True
        if msg_id == 'SetColor':
            self.set_color(*args, **kwargs)
            return True
        if msg_id == 'WaitEnable':
            self.wait_enable(*args, **kwargs)
            return True


    def set_color(self, color):
        assert color in ('Blue', 'Violet', 'Menu'), "Only 'Blue', 'Violet' and 'Menu' colors can use."
        from Core import engine
        engine.cursor.color = color


    def enable(self):
        from Core import engine
        engine.cursor.is_enabled = True
        self.update_begin = self.normal_begin_update
        self.update_end = self.normal_end_update
        self.detach_sequence()


    def disable(self):
        self.update_begin = lambda dt: None
        self.update_end = lambda dt: None
        from Core import engine
        engine.cursor.is_enabled = False
        self.detach_sequence()


    def normal_begin_update(self, dt):
        self.process_regions()


    def normal_end_update(self, dt):
        GameObject.update(self, dt)


    def get_sequence_name(self):
        return self.sequence_name


    def begin_unload_location(self, location_name=None):
        self.detach_sequence()
        self.wait_enable(False)


    def end_load_location(self, location_name=None):
        self.enable()


    def begin_load_location(self, location_name=None):
        self.clear_group('Default')
        self.change_load_group('Default')


    def attach_sequence(self, name, sequence, detach_callback=None):
        self.detach_sequence()
        self.detach_callback = detach_callback
        self.sequence_name = name
        self.holder.sequences['Stay'] = sequence
        self.holder.states['Stay'] = State('Stay')
        self.holder.state = 'Stay'


    def detach_sequence(self):
        self.holder.state = '__empty__'
        self.holder.states['Stay'] = State(None)
        self.sequence_name = None
        if self.detach_callback:
            self.detach_callback()
            self.detach_callback = None


    def hide_sequence(self, flag):
        if flag:
            self.holder.state = '__empty__'
        else:
            if self.holder.states.has_key('Stay'):
                self.holder.state = 'Stay'

    
    def onUnprocessedItemClick(self):
        import Core
        if Core.active_character is not None:
            self.cursor.sndWrong_click.play()
            Core.active_character.playBadReaction()
