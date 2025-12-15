'''
Location class
'''
import wx, cPickle as pickle, os, os.path, Lib
from Misc import ItemBase, PositionDialog
from Lib.Editor import EditorGlobals
from Layer import Layer
import Tanita2, Lib.Globals, Gizmos, shutil
from Lib import config, debug
from weakref import proxy

class Location(ItemBase):
    ''' Location class '''

    def __init__(self, name, parent):
        self.loaded = False
        self.volatile_objects = ['location', 'cursorpos_gizmo', 'childpos_gizmo',
                                 'position_dialog', 'drag']
        self.params = {'width': 1024, 
                       'height': 768,
                       'comment': 'Нет комментария'}
        self.panel_description = ['LOCATION_PROPS', {'width'  : 'WIDTH',
                                                     'height' : 'HEIGHT',
                                                     'comment': 'COMMENT'}]
        self.__position = [0, 0]
        ItemBase.__init__(self, name, parent, wx.ART_LOCATION)
        
        # Loading parameters
        file_name = 'World\\%s\\editor.data' % name
        if os.path.isfile(file_name):
            self.params, temp = pickle.load(file(file_name, 'rb'))
    
    def on_menu(self, event):
        ''' Show context menu '''
        
        if not self.loaded:
            return [('Load',   wx.ART_FILE_OPEN, lambda e: self.load()),
                    (None),
                    ('Delete', wx.ART_DELETE, self.__on_delete),]
        else:
            return [('New layer', wx.ART_LAYER, self.__on_new_layer),
                    (None,),
                    ('Rename'),
                    (None),
                    ('Delete', wx.ART_DELETE, self.__on_delete),]
    
    def get_object(self): return self.location
    
    def load(self):
        if not EditorGlobals.browser_window.prepare_location_load():
            return
        import time
        t = time.clock()
        splash = wx.SplashScreen(wx.ArtProvider.GetBitmap(wx.ART_LOCATION_LOAD),
                                 wx.SPLASH_CENTRE_ON_PARENT |
                                 wx.SPLASH_NO_TIMEOUT, 0, None)
        Lib.parent_window.SetCursor(wx.HOURGLASS_CURSOR)
        
        self.tree.SetItemBold(self.item)
        self.loaded = True
        self.create_location()
        
        file_name = 'World\\%s\\editor.data' % self.name
        if os.path.isfile(file_name):
            temp, self.children = pickle.load(file(file_name, 'rb'))
            def create_volatile_objects(obj):
                for n, c in obj.children.iteritems():
                    c.create_volatile_objects(obj)
                    create_volatile_objects(proxy(c))
            create_volatile_objects(proxy(self))
        self.on_panel_show()
        
        while time.clock() - t < 1.0: pass
        splash.Close()
        Lib.parent_window.SetCursor(wx.STANDARD_CURSOR)
        
        def lock_all(parent):
            parent.lock(True)
            for c in parent.children.itervalues():
                lock_all(c)
        lock_all(self)
        self._update_item_order()
    
    def __on_new_layer(self, event):
        self.track()
        name = self.guess_name(self.children, 'Layer')
        self.children[name] = Layer(name, self)
        
        self.tree.SelectItem(self.children[name].item)
    
    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
        
        self.track()
        self.unload()
        self.tree.Delete(self.item)
        del self.parent.children[self.name]
        
        if os.path.isdir('World/%s' % self.name):
            try: shutil.rmtree('World/%s' % self.name)
            except: pass
        
    def __on_width_change(self, event):
        new_w = self.panel.width.GetValue()
        if new_w == self.params['width']: return
        
        self.track()
        self.params['width'] = int(self.panel.width.GetValue())
        self.location.width = self.params['width']
        self.location.gizmo.width = self.location.width
        
    def __on_height_change(self, event):
        new_h = self.panel.height.GetValue()
        if new_h == self.params['height']: return
        
        self.track()
        self.params['height'] = int(self.panel.height.GetValue())
        self.location.height = self.params['height']
        self.location.gizmo.height = self.location.height
        
    def create_location(self):
        ''' Create location game object '''
        
        EditorGlobals.browser_window.loaded_location = proxy(self)
        
        self.location = Tanita2.Location()
        self.location.width = self.params['width']
        self.location.height = self.params['height']
        self.location.gizmo = Gizmos.Gizmo(self.location.width,
                                           self.location.height, 0x20000000)
        self.__position = getattr(EditorGlobals, '_location_position',
                                  self.__position)[:]
        self.location.position = Tanita2.vec2(self.__position[0], self.__position[1])
        # Cursor position
        self.cursorpos_gizmo = Gizmos.OnscreenText(208, 17, 0xff000000, 0xffffffff)
        self.cursorpos_gizmo.position = Tanita2.vec2(0, 751)
        
        # Object position
        self.childpos_gizmo = Gizmos.OnscreenText(250, 17, 0xff000000, 0xffffffff)
        self.childpos_gizmo.position = Tanita2.vec2(0, 0)
        
        # Loading position dialog
        self.position_dialog = PositionDialog()
    
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        ItemBase.create_volatile_objects(self, parent, controls=[])

        class DragData:
            ''' Dragging information keeper '''
            def __init__(self):
                self.pressed = [False] * 3
                self.pressed_pos = [(0, 0)] * 3
                self.old_pos = [(0, 0)] * 3
                self.delta_pos = [(0, 0)] * 3
                self.kbd_offset = [0, 0]
                self.pressed_selection = False
                self.block_dragging = False
        self.drag = DragData()
        
        if not self.loaded: return
        self.tree.SetItemBold(self.item)
        self.create_location()
    
    def save(self):
        if not self.loaded: return
        params = self.params
        children = self.children
        def reset(obj):
            if getattr(obj, 'children', False):
                for o in obj.children.itervalues():
                    reset(o)
            if getattr(obj, 'item_is_selected', False):
                obj.is_locked = False
            if getattr(obj, 'item_is_expanded', False):
                obj.item_is_expanded = False
        reset(children)

        if not os.path.isdir('World\\%s' % self.name):
            os.mkdir('World\\%s' % self.name)
        try:
            pickle.dump((params, children),
                        file('World\\%s\\editor.data.~tmp' % self.name, 'wb'), 0)
        except:
            wx.MessageBox('Unhanled exception while saving location data.\n' +
                          'All your changes will be lost. Traceback follows.', 'Error',
                          wx.ICON_ERROR | wx.OK)
            raise
        else:
            pickle.dump((self.params, self.children),
                        file('World\\%s\\editor.data' % self.name, 'wb'), 0)
            os.unlink('World\\%s\\editor.data.~tmp' % self.name)

    def on_cleanup(self):
        self.unload()
    
    def unload(self):
        ''' Unload location '''
        if not self.loaded: return
        self.save()
        self.loaded = False
        
        if not os.path.isdir('World\\%s' % self.name):
            os.mkdir('World\\%s' % self.name)
        self.loaded = False
        try:
            pickle.dump((self.params, self.children),
                        file('World\\%s\\editor.data.~tmp' % self.name, 'wb'), 0)
        except:
            wx.MessageBox('Unhanled exception while saving location data.\n' +
                          'All your changes will be lost. Traceback follows.', 'Error',
                          wx.ICON_ERROR | wx.OK)
            raise
        else:
            pickle.dump((self.params, self.children),
                        file('World\\%s\\editor.data' % self.name, 'wb'), 0)
            os.unlink('World\\%s\\editor.data.~tmp' % self.name)

        EditorGlobals.browser_window.loaded_location = None
        self.tree.DeleteChildren(self.item)
        self.children.clear()
        del self.location, self.cursorpos_gizmo, self.childpos_gizmo
        self.tree.SetItemBold(self.item, False)
        
    def on_move_request(self, x_direction, y_direction, shift_pressed):
        if shift_pressed: x_direction *= 20; y_direction *= 20
        self.drag.kbd_offset = [x_direction, y_direction]
        
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_TEXT, self.__on_width_change, self.panel.width)
        self.panel.window.Bind(wx.EVT_TEXT, self.__on_height_change, self.panel.height)
        
        self.panel.window.Enable(self.loaded)
        self.panel.comment.SetValue(self.params['comment'])
        self.panel.width.SetValue(self.params['width'])
        self.panel.height.SetValue(self.params['height'])
        
    def on_panel_hide(self):
        self.params['comment'] = self.panel.comment.GetValue()
        self.params['width'] = int(self.panel.width.GetValue())
        self.params['height'] = int(self.panel.height.GetValue())
        
    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        self.__position = list(new_pos)
        self.location.position = Tanita2.vec2(new_pos[0], new_pos[1])
        EditorGlobals._location_position = self.__position[:]
        
    def draw(self, dt):
        ''' Draw location '''
        
        assert self.loaded, 'Attempt to draw unloaded location!'
        from Lib.Globals import cursor_position
        
        # Mouse wheel handling (zooming)
        if Lib.Globals.mouse_buttons & 8: Lib.Globals.zoom *= 1.1
        elif Lib.Globals.mouse_buttons & 16: Lib.Globals.zoom /= 1.1
        if Lib.Globals.zoom < 1.05 and Lib.Globals.zoom > 0.95 or \
           Lib.Globals.mouse_buttons & 4:
            Lib.Globals.zoom = 1.0
        
        # Mouse position text
        self.cursorpos_gizmo.text = ' Mouse position: (%4d, %4d) ' % \
                                       (int(Lib.Globals.cursor_position.x),
                                        int(Lib.Globals.cursor_position.y))
        
        # Left click - selection
        select_button = 0
        if Lib.Globals.mouse_buttons & (1 << select_button):
            if not self.drag.pressed_selection:
                self.drag.pressed_selection = True
                skip_selection = False
                
                item = self.tree.GetSelection()
                elm = None
                if item and item.IsOk():
                    elm = self.tree.GetPyData(item)
                    if getattr(elm, 'do_handle_click', False):
                        if elm.do_handle_click(cursor_position):
                            skip_selection = True
                            Lib.Globals.mouse_buttons &= 0xFE
                            self.drag.block_dragging = True
                
                if not skip_selection:
                    def inside_child(obj, is_toplevel=False):
                        for c in reversed(obj.children.itervalues()):
                            if is_toplevel and not c.is_visible: continue
                            
                            result = inside_child(c)
                            if result: return result
                            if not c.is_locked and \
                               getattr(c, 'is_inside', lambda pos: False)(cursor_position):
                                return c
                        return None
                    selected_child = inside_child(self, True)
                    if selected_child:
                        self.tree.SelectItem(selected_child.item)
                        selected_child.is_selected = True
                    elif not self.childpos_gizmo.is_inside(cursor_position):
                        if elm: elm.is_selected = False
                        self.tree.Unselect()
        else:
            self.drag.pressed_selection = False
            self.drag.block_dragging = False
        
        # Right click
        right_button = 1
        if Lib.Globals.mouse_buttons & (1 << right_button):
            item = self.tree.GetSelection()
            if item and item.IsOk():
                elm = self.tree.GetPyData(item)
                if getattr(elm, 'do_handle_click', False):
                    if elm.do_handle_click(cursor_position, right_button=True):
                        Lib.Globals.mouse_buttons &= 0xFD
        
        # Child object position text
        item = self.tree.GetSelection()
        selected_movable = False
        elm = None
        if item and item.IsOk():
            elm = self.tree.GetPyData(item)
            if not elm or elm.__class__ is Location: elm = None
            from Project import Project
            if elm and getattr(elm, 'get_position', None):
                class_name = str(elm.__class__)
                class_name = class_name[class_name.rfind('.')+1:]
                pos = elm.get_position()
                self.childpos_gizmo.text = ' %s position: (%4d, %4d) ' % \
                                       (class_name, pos[0], pos[1])
                selected_movable = True
        # elm is current selected object or None for location
        
        # Position dialog box
        if not selected_movable:
            self.childpos_gizmo.text = ' No movable object selected '
        elif Lib.Globals.mouse_buttons & 1:
            if self.childpos_gizmo.is_inside(cursor_position) and \
               Lib.Globals.mouse_buttons & 1 and not self.position_dialog.is_shown():
                self.position_dialog.show(elm)
            elif self.position_dialog.is_shown(): self.position_dialog.hide()
            
        # Moving by keyboard
        if elm and [0, 0] != self.drag.kbd_offset and \
           getattr(elm, 'get_position', False):
            pos = elm.get_position()
            elm.set_position([pos[0] + self.drag.kbd_offset[0],
                              pos[1] + self.drag.kbd_offset[1]])
            self.drag.kbd_offset = [0, 0]
        
        # Mouse dragging clients (for each button)
        drag_clients = [elm, self, None]
        
        # Mouse dragging handling
        for i in xrange(3):
            if i == select_button and self.drag.block_dragging: continue
            
            client = drag_clients[i]
            if getattr(client, 'get_drag_client', False):
                client = client.get_drag_client(cursor_position,
                    Lib.Globals.mouse_buttons & (1 << i) and not self.drag.pressed[i])
            if not client or not getattr(client, 'get_position', None): continue
            
            if Lib.Globals.mouse_buttons & (1 << i):
                if not self.drag.pressed[i]:
                    if not getattr(client, 'is_inside', lambda pos: True)(cursor_position):
                        continue
                    
                    if client.__class__ is not Location: self.track()
                    self.drag.pressed[i] = True
                    self.drag.pressed_pos[i] = (cursor_position.x, cursor_position.y)
                    self.drag.old_pos = client.get_position()[:]
                else:
                    new_pos_x = self.drag.old_pos[0] + cursor_position.x - self.drag.pressed_pos[i][0]
                    new_pos_y = self.drag.old_pos[1] + cursor_position.y - self.drag.pressed_pos[i][1]
                    client.set_position([new_pos_x, new_pos_y])
                
                # Disabling simultaneous dragging by different buttons
                Lib.Globals.mouse_buttons = (1 << i)
            else:
                self.drag.pressed[i] = False

        # Clipping coordinates
        if Lib.Globals.zoom == 1:
            new_pos = self.get_position()
            if self.__position[0] > 0: new_pos[0] = 0
            if self.__position[1] > 0: new_pos[1] = 0
            if self.__position[0] - 1024 < -self.params['width']:
                new_pos[0] = -self.params['width'] + 1024
            if self.__position[1] - 768 < -self.params['height']:
                new_pos[1] = -self.params['height'] + 768
            self.set_position(new_pos)
        
        # Drawing
        self.location.begin_update()
        
        self.location.gizmo.update(dt)
        for o in self.children.itervalues():
            if not o.is_visible: continue
            if Lib.Globals.zoom == 1: # Parallax
                o.layer.position.x = self.location.position.x * o.layer.parallax.x
                o.layer.position.y = self.location.position.y * o.layer.parallax.y
            else: o.layer.position = Tanita2.vec2(0, 0)
            o.layer.update(dt)
        self.location.end_update()
        self.cursorpos_gizmo.update(dt)
        self.childpos_gizmo.update(dt)
        
    def check(self):
        if self.loaded and not self.params['comment']:
            return 'Location %s: no description provided' % self.name
        
    def export(self, path):
        path = os.path.join(path, self.name)
        if not os.path.isdir(path): os.mkdir(path)
        
        j = file(os.path.join(path, '__init__.py'), 'wt')
        j.write(
'''# This file is generated automatically.
# Please don't edit it by hand because your
# changes will be rewritten by editor.

from Core import *
from %s import %s as User%s

"""
%s
%s

"""

class %s(Location, User%s):
    def __init__(self):
        # Initializing global base class
        Location.__init__(self)
        
        # Location properties
        self.name   = "%s"
        self.width  = %d
        self.height = %d

        # Layers
''' % (self.escape(self.name), self.escape(self.name), 
       self.escape(self.name), self.escape(self.params['comment']),
       self.escape(self.name), self.escape(self.name), 
       self.escape(self.name), self.escape(self.name), 
       self.params['width'], self.params['height']))
        
        for layer in self.children.itervalues():
            j.write(
"""        from %sLayer import %sLayer
        self.objects['%s'] = %sLayer()

""" % (layer.name, layer.name, layer.name, layer.name))
            layer.export(os.path.join(path, '%sLayer' % layer.name))

        j.write(
"""        # Initializing user base class
        User%s.__init__(self)
""" % self.escape(self.name))

        j.close()


        # Template for user script file
        if not os.path.exists(os.path.join(path, '%s.py' % self.name)):
            j = file(os.path.join(path, '%s.py' % self.name), 'wt')
            j.write(
"""# Generated automatically.
# This file can be edited safely.

from Core import *

class %s:
    def __init__(self):
        # Todo: Write class specific initialization,
        # create additional states, redefine handlers and
        # links for states generated by editor.
        pass
""" % (self.name))
            j.close()

