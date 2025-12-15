'''
Region class
'''
from weakref import proxy
import wx, Tanita2, Gizmos, Lib.Globals
from Lib.Editor import EditorGlobals
from Misc import ItemBase
from Lib import debug

class Region(ItemBase):
    ''' Region class '''
    
    cursors = ['Normal', 'Active', 'Take', 'Apply', 'Ignore', 'Auto']
    
    def __init__(self, name, parent):
        self.__position = [0, 0]
        self.is_fixed = False
        self.points = []
        self.old_drag_client = None
        self.type = 'Normal'
        self.cursor = Region.cursors.index('Active')
        self.volatile_objects = ['region', 'gizmo', 'old_drag_client', '_pathfind_start_point']
        self.panel_description = ['REGION_PROPS', {'type'  : 'TYPES', 'cursor': 'CURSOR'}]
        ItemBase.__init__(self, name, parent, wx.ART_REGION)

    def do_handle_click(self, position, right_button=False):
        if self.is_fixed:
            if not right_button and None != getattr(self.region.edge_gizmo, 'nearest_i', None) and \
               self.region.edge_gizmo.is_inside(Lib.Globals.cursor_position):
                self.track()
                self.region.insert(self.region.edge_gizmo.nearest_i, self.region.edge_gizmo.point_pos)
                self.points.insert(self.region.edge_gizmo.nearest_i,
                                   (self.region.edge_gizmo.point_pos.x,
                                    self.region.edge_gizmo.point_pos.y))
                return True
            if right_button and len(self.points) > 3:
                for i in xrange(len(self.region.gizmos)):
                    if self.region.gizmos[i].is_inside(Lib.Globals.cursor_position):
                        self.track()
                        del self.region[i]
                        del self.points[i]
                        break
            if self.type != 'Walk' or not self.region.is_point_inside(position): return False
            if right_button:
                self._pathfind_start_point = None
                return False
            for i in xrange(len(self.region.gizmos)):
                g = self.region.gizmos[i]
                if g.is_inside(position): return False
            self._pathfind_start_point = Tanita2.vec2(position)
            return True
        
        # Not fixed
        if right_button:
            if len(self.region) < 3:
                self.tree.Delete(self.item)
                del self.parent.get_object().objects[self.name]
                del self.parent.children[self.name]
                return True
            self.is_selected = False
            self.tree.Unselect()
            self.is_fixed = True
        else:
            if len(self.region) >= 3: self.track()
            location = EditorGlobals.browser_window.loaded_location
            point = self.region.to_local_coordinates(position)# - location.location.position)
            self.region.push(point)
            self.points.append((point.x, point.y))
        return True
        
    def is_inside(self, pos):
        return self.region.is_point_inside(pos) or \
               [True for g in self.region.gizmos if g.is_inside(pos)]
    
    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        self.__position = list(new_pos)
        self.region.position = Tanita2.vec2(new_pos[0], new_pos[1])

    def rgn_path_ID(self, path=None):
        if path:
            full_name = path.split('\\')[1]
        else:
            full_name = self.rgn_path.split('\\')[1]
        name = full_name.split('.')[0]
        return "ResourceId(0x%s, RESOURCE_TYPE_RGN)" % (name.lower())
        
    
    def get_drag_client(self, position, is_click):
        if not is_click: return self.old_drag_client
        self.old_drag_client = self
        
        for i in xrange(len(self.region.gizmos)):
            g = self.region.gizmos[i]
            if g.is_inside(position):
                class GizmoProxy:
                    def __init__(self, parent, index):
                        self.parent = parent
                        self.index = index
                        self.parent.region.gizmos[self.index].is_selected = True
                    def get_position(self):
                        return [self.parent.region[self.index].x,
                                self.parent.region[self.index].y]
                    def set_position(self, new_pos):
                        self.parent.points[self.index] = new_pos[:]
                        self.parent.region[self.index] = Tanita2.vec2(new_pos[0], new_pos[1])
                        self.parent.region.gizmos[self.index].position = Tanita2.vec2(new_pos[0], new_pos[1])
                    def __del__(self):
                        if len(self.parent.region) > self.index:
                            self.parent.region.gizmos[self.index].is_selected = False
                
                self.old_drag_client = GizmoProxy(self, i)
                break
        return self.old_drag_client

    def on_menu(self, event):
        ''' Show context menu '''
        return [('Rename'),
                (None),
                ('Delete', wx.ART_DELETE, self.__on_delete),]
    
    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
        
        self.track()
        self.tree.Delete(self.item)
        del self.parent.get_object().objects[self.name]
        del self.parent.children[self.name]
    
    def get_object(self): return self.region
    
    def _get_pos_object(self): return self.__position
    def on_end_drag(self, over_object):
        from AnimatedObject import AnimatedObject
        return ItemBase.on_end_drag(self, over_object, [AnimatedObject], True)
        
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        self.panel_description = ['REGION_PROPS', {'type'  : 'TYPES', 'cursor': 'CURSOR'}]
        
        # Compatibility layer
        if not hasattr(self, 'type'): self.type = 'Normal'
        if not hasattr(self, 'cursor'): self.cursor = 0
        
        try:
            if -1 == self.volatile_objects.index('_pathfind_start_point'): raise Error
        except:
            self.volatile_objects.append('_pathfind_start_point')
        
        self._pathfind_start_point = None
        
        ItemBase.create_volatile_objects(self, parent)
        self.old_drag_client = None
        
        RegionType = self.type != 'Walk' and Gizmos.Region or Gizmos.PathFindRegion
        self.parent.get_object().objects[self.name] = RegionType(self)
        
        self.region = proxy(self.parent.get_object().objects[self.name])
        self.region.position = Tanita2.vec2(self.__position[0], self.__position[1])
        for px, py in self.points:
            self.region.push(Tanita2.vec2(px, py))

    def check(self):
        parent = self.parent.name
        if not self.type: return '%s -> Region %s: no type specified' % (parent, self.name)
        if not len(self.region): return '%s -> Region %s: region is empty' % (parent, self.name)
        if self.cursor < 0 or self.cursor > 5:
            return '%s -> Region %s: invalid cursor specified' % (parent, self.name)
    
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_COMBOBOX, self.__on_region_type)
        sel = ['Normal', 'Z', 'Block', 'Walk', 'Junction']
        if self.type == 'Junction':
            self.cursor = Region.cursors.index('Normal')
        self.panel.type.SetSelection(sel.index(self.type))
        self.panel.cursor.SetSelection(self.cursor)
        if self.type != 'Normal': self.panel.cursor.Disable()
        else: self.panel.cursor.Enable()
        
    def __on_region_type(self, event):
        old_type = self.type
        self.on_panel_hide()
        if 'Walk' != self.type and 'Walk' != old_type: return
        self._update_item_order()
    
    def on_panel_hide(self):
        sel = ('Normal', 'Z', 'Block', 'Walk', 'Junction')
        i = self.panel.type.GetSelection()
        if wx.NOT_FOUND == i: i = 0
        self.type = sel[i]
        self.region.update_color()
        self.is_fixed = True
        
        if 'Normal' == self.type:
            self.cursor = self.panel.cursor.GetSelection()
            if wx.NOT_FOUND == self.cursor: self.cursor = 0
        if self.type != 'Normal': 
            if self.type == 'Junction':
                self.cursor = Region.cursors.index('Normal')
                self.panel.cursor.SetSelection(self.cursor)                
            self.panel.cursor.Disable()
        else: 
            self.panel.cursor.Enable()

    def dump(self, prefix, path):
        ''' Generating string for writing to __init__.py '''

        import os
        type = ((self.type == 'Normal' or self.type == 'Junction') and [''] or [self.type])[0]
        path = 'art\\%x.rgn' % self.hash(os.path.join(path, '%s.rgn' % self.name))
        cursor_name = Region.cursors[self.cursor]
        cursor = (type == '') and '%srgn.cursor = %d # %s\n' % (prefix, self.cursor, cursor_name) or ''
        self.region.save(path)
        return \
"""%s# '%s' region
%srgn = self.objects['%s'] = %sRegion()
%srgn.load(%s)
%srgn.position = vec2(%f, %f)
%s%sself.reg%s = rgn

""" % ( \
       prefix, self.name, \
       prefix, self.name, type, \
       prefix, self.rgn_path_ID(path), \
       prefix, int(self.get_position()[0]), int(self.get_position()[1]), \
       cursor, \
       prefix, self.name \
    )
