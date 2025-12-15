'''
SequenceSound class
'''
from weakref import proxy
import wx, Tanita2, Gizmos, Lib, os.path
from Lib.Editor import EditorGlobals
from Misc import ItemBase
from Sound import Sound

class SequenceSound(ItemBase):
    ''' SequenceSound class '''
    
    def __init__(self, name, parent):
        self.frame_index = 0
        self.sound_name = None
        self.sound_enabled = True
        ItemBase.__init__(self, name, parent, wx.ART_SOUND_SEQ)
    
    def on_menu(self, event):
        ''' Show context menu '''
        return [('Delete', wx.ART_DELETE, self.__on_delete),]
    
    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
       
        self.track()
        self.tree.Delete(self.item)
        if self.sound_name:
            self.parent._get_seq().del_sound(self.frame_index, self.sound_ref)
        del self.parent.children[self.name]
        
    def __on_sound_select(self, e):
        old_name = self.sound_name
        
        sel = self.panel.sounds.GetSelection()
        if wx.NOT_FOUND == sel:
            self.sound_name = None
        else:
            self.sound_name = self.panel.sounds.GetString(sel)
        if 'None' == self.sound_name: self.sound_name = None
        
        if old_name == self.sound_name: return
       
        if old_name:
            self.parent._get_seq().del_sound(self.frame_index, self.sound_ref)

        if self.sound_name:
            self.sound_ref = self.parent.parent.animation.objects[self.sound_name].sounds[self.sound_name]
            self.parent._get_seq().add_sound(self.frame_index, self.sound_ref)
            self.tree.SetItemText(self.item, '* %s '% self.sound_name)
        else: self.tree.SetItemText(self.item, 'No sound')
    
    def __on_spin(self, e):
        self.parent._get_seq().del_sound(self.frame_index, self.sound_ref)
        self.frame_index = self.panel.frame.GetValue()
        self.parent._get_seq().add_sound(self.frame_index, self.sound_ref)
        
    def __on_checkbtn(self, e):
        self.sound_enabled = self.panel.play_always.GetValue()
        self.parent.parent.children[self.sound_name].play_always = self.sound_enabled
    
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_COMBOBOX, self.__on_sound_select)
        self.panel.window.Bind(wx.EVT_SPINCTRL, self.__on_spin)
        self.panel.window.Bind(wx.EVT_CHECKBOX, self.__on_checkbtn)

        self.panel.frame.SetRange(0, self.parent.parent.animation.sequences[self.parent.name].frame_count-1)
        self.panel.frame.SetValue(self.frame_index)
        
        self.panel.play_always.SetValue(self.sound_enabled)
        
        self.panel.sounds.Clear()
        sel_i = 0
        index = 0
        self.panel.sounds.Append('None')
        for i in self.parent.parent.children.itervalues():
            if i.__class__ is Sound:
                self.panel.sounds.Append(i.name)
                if i.name == self.sound_name: sel_i = index
            index += 1
        self.panel.sounds.Select(sel_i)
    
    def on_panel_hide(self):
        self.frame_index = self.panel.frame.GetValue()
        self.sound_enabled = self.panel.play_always.GetValue()

        sel = self.panel.sounds.GetSelection()
        if wx.NOT_FOUND == sel: return

        self.sound_name = self.panel.sounds.GetString(sel)
        if 'None' == self.sound_name: self.sound_name = None
    
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        self.panel_description = ['SOUNDREF_PROPS', {'sounds' : 'SOUNDS',
                                                     'frame'  : 'FRAME_INDEX',
                                                     'play_always': 'PLAY_ALWAYS'}]

        self.volatile_objects = ['sound_ref']
        ItemBase.create_volatile_objects(self, parent, controls=[])
       
        if self.sound_name:
            self.sound_enabled = self.parent.parent.children[self.sound_name].play_always
            self.sound_ref = self.parent.parent.animation.objects[self.sound_name].sounds[self.sound_name]
            self.parent._get_seq().add_sound(self.frame_index, self.sound_ref)
            self.tree.SetItemText(self.item, '* %s '% self.sound_name)
        else: self.tree.SetItemText(self.item, 'No sound')
    
    def check(self):
        name = '.'.join([self.parent.parent.name, self.parent.name, self.name])
        if not self.sound_name:
            return 'SoundRef %s: no sound selected' % name
        if not self.parent.parent.children.has_key(self.sound_name):
            return 'SoundRef %s: Sound %s doesn\' exist' % (name, self.sound_name)
        if self.parent.parent.children[self.sound_name].looped:
            return 'SoundRef %s: sounds attached to animations couldn\'t be looped' % name
        if self.parent.parent.animation.sequences[self.parent.name].frame_count <= self.frame_index:
            return 'SoundRef %s: sound attached to unexisting frame' % name
