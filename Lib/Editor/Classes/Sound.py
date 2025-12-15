'''
Sound class
'''
from weakref import proxy
import wx, Tanita2, Gizmos, Lib
from Lib.Editor import EditorGlobals
from Misc import ItemBase

class Sound(ItemBase):
    ''' Sound class '''
    
    def __init__(self, name, parent, sound_path, original_path=''):
        self.sound_path = sound_path[:]
        self.original_path = original_path
        self.__position = [0, 0]
        self.looped = False
        self.prolonged = True
        self.play_when_load = False
        self.volume = 100
        self.pan = 0
        
        self.play_always = False
        ItemBase.__init__(self, name, parent, wx.ART_SOUND)
    
    def is_inside(self, pos): return self.gizmo.is_inside(pos)
    
    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        self.__position = list(new_pos)
        self.gizmo.position = Tanita2.vec2(new_pos[0], new_pos[1])

    def sound_path_ID(self):
        full_name = self.sound_path.split('\\')[1]
        name = full_name.split('.')[0]
        return "ResourceId(0x%s, RESOURCE_TYPE_WAV)" % (name.lower())
    
    def on_menu(self, event):
        ''' Show context menu '''
        return [('Rename', wx.ART_RENAME, self.__on_rename),
                (None),
                ('Delete', wx.ART_DELETE, self.__on_delete),]
    
    def __on_rename(self, event):
        ''' Rename self '''
        new_name = EditorGlobals.browser_window.rename_dialog(self.name, self._check_correct_name)
        if not new_name: return
        self.track()
        
        old_name = self.name
        
        self.parent.get_object().objects.change_key(self.name, new_name)
        self.parent.children.change_key(self.name, new_name)
        self.gizmo.sounds.change_key(self.name, new_name)

        self.name = new_name
        self.tree.SetItemText(self.item, self.name)
    
    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
        
        self.track()
        self.tree.Delete(self.item)
        del self.parent.get_object().objects[self.name]
        del self.parent.children[self.name]
        del self.children
        del self.gizmo
        
    def get_object(self): return self.gizmo
    
    def check(self): pass
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        self.panel_description = ['SOUND_PROPS', {'reload' : 'RELOAD_BTN',
                                                  'stop'   : 'STOP',
                                                  'play'   : 'PLAY',
                                                  'looped' : 'LOOPED',
                                                  'prolonged': 'PROLONGED',
                                                  'play_when_load' : 'PLAY_WHEN_LOAD',
                                                  'volume' : 'VOLUME',
                                                  'pan'    : 'PAN',
                                                  'filename' : 'FILENAME',
                                                  'openeditor' : 'EDIT',
                                                  'play_always' : 'PLAY_ALWAYS'}]
        self.volatile_objects = ['gizmo']
        ItemBase.create_volatile_objects(self, parent)
        
        if not hasattr(self, 'play_always'): self.play_always = False
        if not hasattr(self, 'play_when_load') : self.play_when_load = False

        # Initializations
        self.parent.get_object().objects[self.name] = Gizmos.SoundGizmo(self, 50, 50, 0xff004400)
        self.gizmo = proxy(self.parent.get_object().objects[self.name])
        import os.path
        if not os.path.isfile(self.sound_path):
            wx.MessageBox('File not found: "%s"' % self.sound_path, 'Error', wx.OK | wx.ICON_ERROR)
        try: self.gizmo.add_sound(self.name, self.sound_path)
        except:
            wx.MessageBox('Unable to load file. See log file for details', 'Error')
        self.gizmo.position = Tanita2.vec2(self.__position[0], self.__position[1])
        self.gizmo.sounds[self.name].looped = self.looped
        self.gizmo.sounds[self.name].prolonged = self.prolonged
        self.gizmo.sounds[self.name].volume = self.volume
        self.gizmo.sounds[self.name].pan = self.pan

    def __on_checkbox(self, event):
        o = event.GetEventObject()
        if o == self.panel.looped:
            self.looped = o.GetValue()
            self.gizmo.sounds[self.name].looped = self.looped
        elif o == self.panel.prolonged:
            self.prolonged = o.GetValue()
            self.gizmo.sounds[self.name].prolonged = self.prolonged
        elif o == self.panel.play_always:
            self.play_always = o.GetValue()
        elif o == self.panel.play_when_load:
            self.play_when_load = o.GetValue()

    def __on_button(self, e):
        o = e.GetEventObject()
        if o == self.panel.openeditor:
            import os.path
            Tanita2.shell_edit(os.path.abspath(self.sound_path))
        elif o == self.panel.play:
            self.gizmo.sounds[self.name].rewind()
            self.gizmo.sounds[self.name].play()
        elif o == self.panel.stop:
            self.gizmo.sounds[self.name].stop()
        elif o == self.panel.reload:
            del self.gizmo.sounds[self.name]
            flag = Lib.config['disable_file_cache']
            Lib.config['disable_file_cache'] = True
            
            try: self.gizmo.add_sound(self.name, self.sound_path)
            except: wx.MessageBox('Unable to load file. See log file for details', 'Error')
            
            Lib.config['disable_file_cache'] = flag
            
            self.gizmo.sounds[self.name].looped = self.looped
            self.gizmo.sounds[self.name].prolonged = self.prolonged
            self.gizmo.sounds[self.name].volume = self.volume
            self.gizmo.sounds[self.name].pan = self.pan
    
    def __on_slider(self, e):
        o = e.GetEventObject()
        if o == self.panel.volume:
            self.volume = o.GetValue()
            self.gizmo.sounds[self.name].volume = self.volume
        elif o == self.panel.pan:
            self.pan = o.GetValue()
            self.gizmo.sounds[self.name].pan = self.pan
        
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_CHECKBOX, self.__on_checkbox)
        self.panel.window.Bind(wx.EVT_SLIDER, self.__on_slider)
        self.panel.window.Bind(wx.EVT_BUTTON, self.__on_button)
        self.panel.looped.SetValue(self.looped)
        self.panel.prolonged.SetValue(self.prolonged)
        self.panel.play_always.SetValue(self.play_always)
        self.panel.play_when_load.SetValue(self.play_when_load)
        
        self.panel.volume.SetValue(self.volume)
        self.panel.pan.SetValue(self.pan)
        
        self.panel.filename.SetValue(self.sound_path)
    
    def on_panel_hide(self):
        self.looped = self.panel.looped.GetValue()
        self.prolonged = self.panel.prolonged.GetValue()
        self.play_always = self.panel.play_always.GetValue()
        
        self.volume = self.panel.volume.GetValue()
        self.pan = self.panel.pan.GetValue()
