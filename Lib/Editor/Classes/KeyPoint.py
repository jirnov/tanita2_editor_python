'''
Path key point class
'''
import wx
import wx, Tanita2, Gizmos, Lib, os.path
from Lib.Editor import EditorGlobals
from Misc import ItemBase
from weakref import proxy

class KeyPoint(ItemBase):
    ''' Path key point class '''
    
    def __init__(self, name, parent):
        self.__position = [0, 0]
        self.index = 0
        self.speed = 0
        self.volatile_objects = ['gizmo']
        ItemBase.__init__(self, name, parent, wx.ART_POINT)
    
    def on_menu(self, event):
        ''' Show context menu '''
        return [('Rename', wx.ART_RENAME, self.__on_rename),
                (None),
                ('Delete', wx.ART_DELETE, self.__on_delete),]
    
    def __on_rename(self, event):
        ''' Rename self '''
        new_name = EditorGlobals.browser_window.rename_dialog(self.name, 
                                                               self._check_correct_name)
        if not new_name: return
        self.track()
        
        old_name = self.name
        del self.parent.path.key_points[self.name]
        self.parent.path.key_points[new_name] = Tanita2.KeyPoint(self.index, self.speed)
        self.parent.children.change_key(self.name, new_name)
        
        self.name = new_name
        self.tree.SetItemText(self.item, self.name)

    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
        self.track()
        self.tree.Delete(self.item)
        
        del self.parent.path.key_points[self.name]
        del self.parent.children[self.name]
        
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_SPINCTRL, self.__on_index_change, self.panel.index)
        self.panel.window.Bind(wx.EVT_SCROLL_CHANGED, self.__on_speed,  self.panel.speed)
        
        self.panel.index.SetRange(0, len(self.parent.path)-1)
        self.panel.index.SetValue(self.index)
        self.panel.speed.SetValue(self.speed)
    
    def on_panel_hide(self):
        self.index = self.panel.index.GetValue()
        self.speed = self.panel.speed.GetValue()
        
    def __on_index_change(self, e):
        self.index = self.panel.index.GetValue()
        self.parent.path.key_points[self.name].index = self.index
        self.update_points()
        
    def __on_speed(self, e):
        self.speed = self.panel.speed.GetValue()
        self.parent.path.key_points[self.name].speed = self.speed
        
    def update_points(self):
        self.gizmo.position = \
            Tanita2.vec2(self.parent.path[self.index].x-10, self.parent.path[self.index].y-10)

    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        self.panel_description = ['KPOINT_PROPS', {'index'  : 'POINT_INDEX',
                                                   'speed'  : 'SPEED'}]
        was_selected = getattr(self, 'item_is_selected', False)
        self.item_is_selected = False
        ItemBase.create_volatile_objects(self, parent, None)

        self.parent.path.key_points[self.name] = Tanita2.KeyPoint(self.index, self.speed)
        
        self.parent.path.objects[self.name] = Gizmos.SelectionGizmo(self, 20, 20, 0x7f0000ff)
        self.gizmo = proxy(self.parent.path.objects[self.name])
        self.gizmo.position = Tanita2.vec2(self.parent.path[self.index].x-10, self.parent.path[self.index].y-10)

        if was_selected: self.tree.SelectItem(self.item)
        
    def check(self): pass
