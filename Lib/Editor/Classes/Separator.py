'''
Separator class
'''
import wx
from Misc import ItemBase

class Separator(ItemBase):
    ''' Tree item separator class '''
    
    def __init__(self, parent, id="--"):
        ItemBase.__init__(self, '-- %s --' % id, parent, wx.ART_EMPTY)
        self.id = id

    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        if not hasattr(self, 'id'): self.id = "--"
        
        ItemBase.create_volatile_objects(self, parent, controls=[])
        self.tree.SetItemTextColour(self.item, wx.Color(200, 200, 200))
        
    def on_panel_show(self):
        self.tree.SelectItem(self.parent.item)
        
    def check(self): pass
