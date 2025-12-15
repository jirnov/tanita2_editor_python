'''
StaticImage class
'''
from weakref import proxy
import wx, Tanita2, Gizmos
from Misc import ItemBase

class StaticImage(ItemBase):
    ''' StaticImage class '''
    
    def __init__(self, name, parent, image_path, original_path=''):
        self.image_path = image_path[:]
        self.original_path = original_path
        self.__position = [0, 0]
        self.is_compressed = True
        self.volatile_objects = ['image', 'gizmo']
        ItemBase.__init__(self, name, parent, wx.ART_STATIC)
    
    def is_inside(self, pos): return self.image.sequence.is_inside(pos)
    
    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        self.__position = list(new_pos)
        self.image.position = Tanita2.vec2(new_pos[0], new_pos[1])

    def image_path_ID(self):
        full_name = self.image_path.split('\\')[1]
        name = full_name.split('.')[0]
        return "ResourceId(0x%s, RESOURCE_TYPE_PNG)" % (name.lower())
    
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
        del self.image
        
    def get_object(self): return self.image
    
    def check(self): pass
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        self.panel_description = ['STATICIMAGE_PROPS', {'iscomp' : 'IS_COMPRESSED'}]
        ItemBase.create_volatile_objects(self, parent)
        
        # Compatibility layer
        if not hasattr(self, 'original_path'): self.original_path = ''
        if not hasattr(self, 'is_compressed'): self.is_compressed = True
        
        # Initializations
        self.parent.layer.objects[self.name] = Tanita2.LayerImage()
        self.image = proxy(self.parent.layer.objects[self.name])
        import os.path
        if not os.path.isfile(self.image_path):
            wx.MessageBox('File not found: "%s"' % self.image_path, 'Error', wx.OK | wx.ICON_ERROR)
        self.image.load_image(self.image_path, self.is_compressed)
        self.image.position = Tanita2.vec2(self.__position[0], self.__position[1])
        
        self.image.objects['_gizmo_'] = Gizmos.SelectionGizmo(self, self.image.sequence.bounding_box.x, 
                                                              self.image.sequence.bounding_box.y, 0x7fe89590)

    def __on_checkbox(self, event):
        self.track()
        o = event.GetEventObject()
        if o == self.panel.iscomp:
            self.is_compressed = o.GetValue()
            self._update_item_order()
            return
        
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_CHECKBOX, self.__on_checkbox)
        self.panel.iscomp.SetValue(self.is_compressed)
    
    def on_panel_hide(self):
        self.is_compressed = self.panel.iscomp.GetValue()
