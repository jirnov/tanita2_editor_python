'''
Point class
'''
from weakref import proxy
import wx, Tanita2, Gizmos
from Misc import ItemBase

class Point(ItemBase):
    ''' Point class '''
    
    def __init__(self, name, parent):
        self.__position = [0, 0]
        self.volatile_objects = ['gizmo']
        ItemBase.__init__(self, name, parent, wx.ART_POINT)
    
    def is_inside(self, pos):
        return self.gizmo.objects['_gizmo_'].is_inside(pos)
    
    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        self.__position = list(new_pos)
        self.gizmo.position = Tanita2.vec2(new_pos[0]-2, new_pos[1]-2)
    
    def on_menu(self, event):
        ''' Show context menu '''
        return [('Rename'),
                (None),
                ('Delete', wx.ART_DELETE, self.__on_delete),]
    
    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
        
        self.track()
        self.tree.Delete(self.item)
        del self.parent.layer.objects[self.name]
        del self.parent.children[self.name]
        del self.children
        del self.gizmo
    
    def get_object(self): return self.gizmo
    
    def check(self): pass
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        ItemBase.create_volatile_objects(self, parent)
        
        # Initializations
        self.parent.layer.objects[self.name] = Gizmos.Gizmo2(4, 4, 0x7f005500)
        self.gizmo = proxy(self.parent.layer.objects[self.name])
        self.gizmo.position = Tanita2.vec2(self.__position[0]-2, self.__position[1]-2)
        self.gizmo.objects['_gizmo_'] = Gizmos.SelectionGizmo(self, 40, 40, 0x4400ff00)
        self.gizmo.objects['_gizmo_'].position = Tanita2.vec2(-18, -18)
