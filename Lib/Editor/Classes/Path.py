'''
Path class
'''
from weakref import proxy
import wx, Tanita2, Gizmos, Lib.Globals
from Lib.Editor import EditorGlobals
from Misc import ItemBase
from Lib import debug
from KeyPoint import KeyPoint

class Path(ItemBase):
    ''' Path class '''
    
    def __init__(self, name, parent):
        self.__position = [0, 0]
        self.is_fixed = False
        self.points = []
        self.old_drag_client = None
        
        self.affect_pos = True
        self.rel_move = False
        self.affect_rot = True
        self.rel_rot = False
        
        self.volatile_objects = ['path', 'gizmo', 'old_drag_client']
        ItemBase.__init__(self, name, parent, wx.ART_PATH)

    def update_kpoints(self, changed_index=1e9, added=True):
        for k in self.children.itervalues():
            if k.index >= changed_index:
                k.index += added and 1 or -1
                if k.index >= len(self.path):
                    k.index = len(self.path)-1
            k.update_points()

    def do_handle_click(self, position, right_button=False):
        if self.is_fixed:
            if not right_button and None != getattr(self.path.edge_gizmo, 'nearest_i', None) and \
               self.path.edge_gizmo.is_inside(Lib.Globals.cursor_position):
                self.track()
                self.path.insert(self.path.edge_gizmo.nearest_i, self.path.edge_gizmo.point_pos)
                self.points.insert(self.path.edge_gizmo.nearest_i,
                                   (self.path.edge_gizmo.point_pos.x,
                                    self.path.edge_gizmo.point_pos.y))
                self.update_kpoints(self.path.edge_gizmo.nearest_i, True)
                return True
            if right_button and len(self.points) > 2:
                for i in xrange(len(self.path.gizmos)):
                    if self.path.gizmos[i].is_inside(Lib.Globals.cursor_position):
                        self.track()
                        del self.path[i]
                        del self.points[i]
                        self.update_kpoints(i, False)
                        break
            return False
        
        # Not fixed
        if right_button:
            if len(self.path) < 2:
                self.tree.Delete(self.item)
                del self.parent.get_object().objects[self.name]
                del self.parent.children[self.name]
                return True
            self.is_selected = False
            self.tree.Unselect()
            self.is_fixed = True
        else:
            if len(self.path) >= 2: self.track()
            location = EditorGlobals.browser_window.loaded_location
            point = self.path.to_local_coordinates(position)
            self.path.push(point)
            self.points.append((point.x, point.y))
            self.update_kpoints(len(self.path)-1, True)
        return True
    
    def is_inside(self, pos):
        return [True for g in self.path.gizmos if g.is_inside(pos)]
    
    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        self.__position = list(new_pos)
        self.path.position = Tanita2.vec2(new_pos[0], new_pos[1])

    def pth_path_ID(self, pth_path):
        full_name = pth_path.split('\\')[1]
        name = full_name.split('.')[0]
        return "ResourceId(0x%s, RESOURCE_TYPE_PTH)" % (name.lower())
    
    def get_drag_client(self, position, is_click):
        if not is_click: return self.old_drag_client
        self.old_drag_client = self
        
        for i in xrange(len(self.path.gizmos)):
            g = self.path.gizmos[i]
            if g.is_inside(position):
                class GizmoProxy:
                    def __init__(self, parent, index):
                        self.parent = parent
                        self.index = index
                        self.parent.path.gizmos[self.index].is_selected = True
                    def get_position(self):
                        return [self.parent.path[self.index].x,
                                self.parent.path[self.index].y]
                    def set_position(self, new_pos):
                        self.parent.points[self.index] = new_pos[:]
                        self.parent.path[self.index] = Tanita2.vec2(new_pos[0], new_pos[1])
                        self.parent.path.gizmos[self.index].position = Tanita2.vec2(new_pos[0], new_pos[1])
                    def __del__(self):
                        if len(self.parent.path) > self.index:
                            self.parent.path.gizmos[self.index].is_selected = False
                
                self.old_drag_client = GizmoProxy(self, i)
                break
        return self.old_drag_client

    def on_menu(self, event):
        ''' Show context menu '''
        return [('Add keypoint', wx.ART_POINT, lambda e: self.add_keypoint()),
                ('Rename'),
                (None),
                ('Delete', wx.ART_DELETE, self.__on_delete),]
                
    def add_keypoint(self):
        self.track()
        name = self.guess_name(self.children, 'KeyPoint')
        
        self.children[name] = KeyPoint(name, self)
        self.tree.SelectItem(self.children[name].item)
    
    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
        
        self.track()
        self.tree.Delete(self.item)
        del self.parent.get_object().objects[self.name]
        del self.parent.children[self.name]
        del self.parent.get_object().objects[self.__test_gizmo_name]
    
    def get_object(self): return self.path
    
    def _get_pos_object(self): return self.__position
        
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        self.panel_description = ['PATH_PROPS', {'affect_pos': 'AFFECT_POSITION',
                                                 'rel_move':   'RELATIVE_MOVE',
                                                 'affect_rot': 'AFFECT_ROTATION',
                                                 'rel_rot':    'RELATIVE_ROTATION',
                                                 'test':       'TEST'}]
        
        ItemBase.create_volatile_objects(self, parent)
        self.old_drag_client = None
        
        self.parent.get_object().objects[self.name] = Gizmos.Path(self)
        
        self.path = proxy(self.parent.get_object().objects[self.name])
        self.path.position = Tanita2.vec2(self.__position[0], self.__position[1])
        for px, py in self.points:
            self.path.push(Tanita2.vec2(px, py))
        
        self.__test_gizmo_name = self.name+'__test_gizmo'
        self.parent.get_object().objects[self.__test_gizmo_name] = \
            Gizmos.PathTestGizmo(self, 100, 2, 0xffa00000)
        self.path.test_gizmo = self.parent.get_object().objects[self.__test_gizmo_name]

    def check(self):
        if not len(self.path): return 'Path %s: path is empty' % self.name
        if not len(self.path.key_points):
            return 'Path %s: path has no keypoints' % self.name
    
    def on_panel_show(self):
        self.panel.affect_pos.SetValue(self.affect_pos)
        self.panel.rel_move.SetValue(self.rel_move)
        self.panel.affect_rot.SetValue(self.affect_rot)
        self.panel.rel_rot.SetValue(self.rel_rot)
        
        self.panel.window.Bind(wx.EVT_CHECKBOX, self.__hide_show_checkbox)
        self.panel.window.Bind(wx.EVT_BUTTON, self.__test_path)
        self.__hide_show_checkbox(None)
        
    def __hide_show_checkbox(self, e):
        self.affect_pos = self.panel.affect_pos.GetValue()
        self.rel_move = self.panel.rel_move.GetValue()
        self.affect_rot = self.panel.affect_rot.GetValue()
        self.rel_rot = self.panel.rel_rot.GetValue()
        
        if self.affect_pos: self.panel.rel_move.Enable()
        else: self.panel.rel_move.Disable()
        
        if self.affect_rot: self.panel.rel_rot.Enable()
        else: self.panel.rel_rot.Disable()
        
    def __test_path(self, event):
        if not len(self.path): return
        self.path.detach()
        self.path.test_gizmo.position = self.path[0]
        self.path.test_gizmo.rotation = 0
        
        if not len(self.path.key_points):
            self.path.key_points['__start'] = Tanita2.KeyPoint(0, 100)
        else:
            if self.path.key_points.has_key('__start'):
                del self.path.key_points['__start']
        
        self.path.affect_position = self.affect_pos
        self.path.relative_movement = True
        self.path.affect_rotation = self.affect_rot
        self.path.relative_rotation = False
        self.path.attach(self.path.test_gizmo)
    
    def on_panel_hide(self):
        self.is_fixed = True
        self.__hide_show_checkbox(None)
        
        