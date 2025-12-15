'''
Gizmo classes
'''
import Tanita2, Lib.Globals, weakref

_all_regions = []

class Gizmo(Tanita2.Gizmo):
    ''' Gizmo (wrapped for easy constructing) '''
    def __init__(self, w, h, color):
        Tanita2.Gizmo.__init__(self)
        self.width = float(w)
        self.height = float(h)
        self.color = long(color)
        
class Gizmo2(Tanita2.Gizmo):
    ''' Gizmo (wrapped for easy constructing) '''
    def __init__(self, w, h, color):
        Tanita2.Gizmo.__init__(self)
        self.width = float(w)
        self.height = float(h)
        self.color = long(color)
    
    def update(self, dt):
        self.begin_update()
        self.update_children(dt)
        self.end_update()
        Tanita2.Gizmo.update(self, dt)

class OnscreenText(Tanita2.TextObject):
    ''' Text with background unaffected by zoom '''
    
    def __init__(self, w, h, color, bgcolor):
        Tanita2.TextObject.__init__(self)
        self.color = color
        self.back = Gizmo(w, h, bgcolor)
        self.w = w
        self.h = h
    
    def update(self, dt):
        self.w = len(self.text) * 7
        self.back.position = self.position / Lib.Globals.zoom
        self.back.width = self.w / Lib.Globals.zoom
        self.back.height = self.h / Lib.Globals.zoom
        self.back.update(dt)
        Tanita2.TextObject.update(self, dt)
        pass
        
    def is_inside(self, point): return self.back.is_inside(point)

class SelectionGizmo(Gizmo):
    ''' Gizmo for selectable objects '''
    def __init__(self, parent, w, h, color):
        Gizmo.__init__(self, w, h, color)
        self.parent_object = weakref.proxy(parent)
    
    def update(self, dt):
        if not getattr(self.parent_object, 'is_selected', False): return

        self.begin_update()
        self.update_children(dt)
        self.end_update()
        Tanita2.Gizmo.update(self, dt)
        
class AnimationGizmo(SelectionGizmo):
    def update(self, dt):
        if getattr(self.parent_object, 'is_selected', False):
            s = self.parent_object.animation.state
            
            self.begin_update()
            if self.parent_object.affect_pivot:
                self.parent_object.animation.objects['_gizmo_'].objects['_gizmo_hotspot_'].update(dt)
            if s != '?__special_state__?':
                self.parent_object.animation.objects['_gizmo_'].objects[s].update(dt)
            self.parent_object.animation.objects['_gizmo_'].objects['_gizmo!'].update(dt)
            self.end_update()
            Gizmo.update(self, dt)
            return
        import Sequence
        name = None
        for i in self.parent_object.children.itervalues():
            if i.__class__ is not Sequence.AnimatedSequence: continue
            if getattr(i, 'is_selected', False): name = i.name; break
        if not name: return

        self.begin_update()
        self.parent_object.animation.objects['_gizmo_'].objects[name].update(dt)
        self.end_update()

class CommonRegion:
    ''' Region with point-gizmos '''
    def __init__(self, parent):
        self.parent_object = parent
        self.gizmos = []
        self.edge_gizmo = SelectionGizmo(self.parent_object, 10, 10, 0x7fff0000)
        self.update_color()
        
        global _all_regions
        _all_regions.append(self)

    def update_color(self):
        # Region colors for different region types (non-selected, selected)
        self.colors = {'Normal':   (0x330000ff, 0xff0000ff),
                       'Z':        (0x55ff00ff, 0xffff00ff),
                       'Block':    (0x33000000, 0xff000000),
                       'Walk':     (0x33ffff00, 0xffffff00),
                       'Junction': (0x7f00ffff, 0xff00ffff)}
        self.normal_color, self.selected_color = self.colors[self.parent_object.type]
        
    def push(self, point):
        self.gizmos.append(SelectionGizmo(self.parent_object, 10, 10, 0x7f0000ff))
        self.gizmos[-1].is_selected = False
        Tanita2.Region.push(self, point)
        
    def insert(self, index, point):
        self.gizmos.insert(index, SelectionGizmo(self.parent_object, 10, 10, 0x7f0000ff))
        self.gizmos[index].is_selected = False
        Tanita2.Region.insert(self, index, point)
        
    def __delitem__(self, index):
        del self.gizmos[index]
        Tanita2.Region.__delitem__(self, index)
        
    def update(self, dt):
        self.color = self.parent_object.is_selected and self.selected_color or self.normal_color
        self._tanita2class.update(self, dt)
        self.begin_update()
        for i in xrange(len(self.gizmos)):
            if self.gizmos[i].is_inside(Lib.Globals.cursor_position) or \
               (Lib.Globals.mouse_buttons & 1 and self.gizmos[i].is_selected):
                self.gizmos[i].color = self.selected_color
            else: self.gizmos[i].color = self.normal_color
            self.gizmos[i].position = Tanita2.vec2(self[i].x - 5, self[i].y - 5)
            self.gizmos[i].update(dt)
        
        # Finding nearest edge and center point
        if self.parent_object.is_fixed:
            nearest_i = None
            nearest_delta2 = 20 ** 2
            nearest_dist2 = nearest_delta2 * 10
            nearest_pos = None
            
            cpos = self.to_local_coordinates(Lib.Globals.cursor_position)
            for i in range(len(self)):
                i2 = (i+1) % len(self)
                if ((self[i].x - self[i2].x) ** 2) + ((self[i].y - self[i2].y) ** 2) <= 40**2:
                    continue
                edge_center = (self[i] + self[i2]) / 2
                
                dist2 = (edge_center.x - cpos.x) ** 2 + (edge_center.y - cpos.y) ** 2
                if nearest_dist2 > dist2:
                    nearest_i = i2
                    nearest_dist2 = dist2
                    nearest_pos = Tanita2.vec2(edge_center)

            if nearest_dist2 < nearest_delta2:
                self.edge_gizmo.position = nearest_pos - Tanita2.vec2(5, 5)
                self.edge_gizmo.update(dt)
                
                self.edge_gizmo.nearest_i = nearest_i
                self.edge_gizmo.point_pos = Tanita2.vec2(nearest_pos)
            else: self.edge_gizmo.nearest_i = None
        self.end_update()

class Region(CommonRegion, Tanita2.Region):
    def __init__(self, parent):
        self._tanita2class = Tanita2.Region
        Tanita2.Region.__init__(self)
        CommonRegion.__init__(self, parent)

class PathFindRegion(CommonRegion, Tanita2.PathFindRegion):
    ''' Path find region with point-gizmos '''
    def __init__(self, parent):
        self._tanita2class = Tanita2.PathFindRegion
        Tanita2.PathFindRegion.__init__(self)
        CommonRegion.__init__(self, parent)
    
    def update(self, dt):
        CommonRegion.update(self, dt)
        
        if not self.parent_object._pathfind_start_point: return
        
        self.block_regions = []
        global _all_regions
        for r in _all_regions: 
            if r.parent_object.type != 'Block': continue
            self.block_regions.append(r)
        
        path = self.find_path(self.parent_object._pathfind_start_point,
                              Lib.Globals.cursor_position)
        path.position += self.position
        path.update(dt)

class Path(Tanita2.Path):
    ''' Path with point-gizmos '''
    
    def __init__(self, parent):
        Tanita2.Path.__init__(self)
        
        self.parent_object = parent
        self.gizmos = []
        self.edge_gizmo = SelectionGizmo(self.parent_object, 10, 10, 0x7fff00ff)
        self.normal_color, self.selected_color = 0x7f550055, 0xff550055

    def push(self, point):
        self.gizmos.append(SelectionGizmo(self.parent_object, 10, 10, 0x7f0000ff))
        self.gizmos[-1].is_selected = False
        Tanita2.Path.push(self, point)
        
    def insert(self, index, point):
        self.gizmos.insert(index, SelectionGizmo(self.parent_object, 10, 10, 0x7f0000ff))
        self.gizmos[index].is_selected = False
        Tanita2.Path.insert(self, index, point)
        
    def __delitem__(self, index):
        del self.gizmos[index]
        Tanita2.Path.__delitem__(self, index)
        
    def update(self, dt):
        self.color = self.parent_object.is_selected and self.selected_color or self.normal_color
        Tanita2.Path.update(self, dt)
        self.begin_update()
        for i in xrange(len(self.gizmos)):
            if self.gizmos[i].is_inside(Lib.Globals.cursor_position) or \
               (Lib.Globals.mouse_buttons & 1 and self.gizmos[i].is_selected):
                self.gizmos[i].color = self.selected_color
            else: self.gizmos[i].color = self.normal_color
            self.gizmos[i].position = Tanita2.vec2(self[i].x - 5, self[i].y - 5)
            self.gizmos[i].update(dt)
        
        # Finding nearest edge and center point
        if self.parent_object.is_fixed:
            nearest_i = None
            nearest_delta2 = 20 ** 2
            nearest_dist2 = nearest_delta2 * 10
            nearest_pos = None
            
            cpos = self.to_local_coordinates(Lib.Globals.cursor_position)
            for i in range(len(self)):
                i2 = (i+1) % len(self)
                if ((self[i].x - self[i2].x) ** 2) + ((self[i].y - self[i2].y) ** 2) <= 40**2:
                    continue
                edge_center = (self[i] + self[i2]) / 2
                
                dist2 = (edge_center.x - cpos.x) ** 2 + (edge_center.y - cpos.y) ** 2
                if nearest_dist2 > dist2:
                    nearest_i = i2
                    nearest_dist2 = dist2
                    nearest_pos = Tanita2.vec2(edge_center)

            if nearest_dist2 < nearest_delta2:
                self.edge_gizmo.position = nearest_pos - Tanita2.vec2(5, 5)
                self.edge_gizmo.update(dt)
                
                self.edge_gizmo.nearest_i = nearest_i
                self.edge_gizmo.point_pos = Tanita2.vec2(nearest_pos)
            else: self.edge_gizmo.nearest_i = None
        self.end_update()
        
        #self.test_gizmo.position = 
        self.test_gizmo.update(dt)

class PathTestGizmo(SelectionGizmo):
    ''' Gizmo for path testing '''
    
    def __init__(self, parent, w, h, color):
        SelectionGizmo.__init__(self, parent, w, h, color)
    
    def update(self, dt):
        if not self.parent_object.path.is_playing: return
        SelectionGizmo.update(self, dt)

class SoundGizmo(Tanita2.Gizmo):
    ''' Gizmo (wrapped for easy constructing) '''
    def __init__(self, parent, w, h, color):
        Tanita2.Gizmo.__init__(self)
        self.width = float(w)
        self.height = float(h)
        self.color = long(color)
        self.parent_object = parent
        
    def update(self, dt):
        if not getattr(self.parent_object, 'is_selected', False) and \
           not self.parent_object.play_always: return
        
        self.begin_update()
        self.update_sounds(dt)
        self.update_children(dt)
        self.end_update()
        if getattr(self.parent_object, 'is_selected', False):
            Tanita2.Gizmo.update(self, dt)
