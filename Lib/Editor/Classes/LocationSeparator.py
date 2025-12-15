'''
Location class
'''
import wx, cPickle as pickle, os, os.path, Lib
from Misc import ItemBase, PositionDialog
from Lib.Editor import EditorGlobals
import Tanita2, Lib.Globals, Gizmos, shutil
from Lib import config, debug
from weakref import proxy

class LocationSeparator(ItemBase):
    ''' LocationSeparator class '''
    def __init__(self, name, parent):
        self.__position = [0, 0]
        self.volatile_objects = ['locationseparator', 'drag', 'position_dialog']
        ItemBase.__init__(self, name, parent, wx.ART_EMPTY)

    def create_volatile_objects(self, parent, controls=[]):
        ItemBase.create_volatile_objects(self, parent, controls=[])
        self.tree.SetItemTextColour(self.item, wx.Color(200, 200, 200))
        self.tree.SetItemText(self.item, '-- ' + self.name + ' --')

    def on_menu(self, event):
        ''' Show context menu '''
        return [('Rename', wx.ART_RENAME, self.__on_rename),
                (None,),                
                ('Delete', wx.ART_DELETE, self.__on_delete),]

    def __on_rename(self, event):
        new_name = EditorGlobals.browser_window.rename_dialog(self.name, self._check_correct_name)        
        if new_name:
            self.track()
            if self.parent:
                self.parent.children.change_key(self.name, new_name)
                if hasattr(self.parent, 'get_object'):
                    self.parent.get_object().objects.change_key(self.name, new_name)
            self.name = new_name
            self.tree.SetItemText(self.item, '-- ' + self.name + ' --')

    def __on_delete(self, event):
        self.track()
        self.tree.Delete(self.item)
        del self.parent.children[self.name]

    def check(self):
        pass

    def unload(self):
        pass

    def loaded(self):
        pass
