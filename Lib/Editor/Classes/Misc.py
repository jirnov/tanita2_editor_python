'''
Miscellaneous definitions
'''
import wx, weakref, os, Lib, Lib.Editor.Commons
import Tanita2, Lib.Globals as Globals
from Lib.Editor import EditorGlobals
from Lib import config

class ItemBase:
    ''' Base class for tree items '''
    
    def __init__(self, name, parent, resource_name):
        self.art = resource_name
        self.name = name
        self.children = OrderedDict()
        self.is_selected = False
        self.is_locked = False
        self.create_volatile_objects(parent)
        
    def create_volatile_objects(self, parent, controls=['lock']):
        ''' Create all non-persistent objects: tree items, game objects.
            Volatile objects are objects that are not saved between
            history changes and are generated on fly from saved data '''
        self.tree = EditorGlobals.browser_window.tree
        self.parent = parent
        
        self.controls = {}
        wnd = None
        if controls:
            # Creating control icons panel (eye, lock etc)
            wnd = wx.Panel(self.tree)
            wnd.SetBackgroundColour(self.tree.GetBackgroundColour())
            szr = wx.BoxSizer(wx.HORIZONTAL)
            wnd.SetSizer(szr)
            szr.Add((5, 5))
            if 'lock' in controls:
                w = wx.StaticBitmap(wnd, -1, wx.ArtProvider.GetBitmap(
                                    self.is_locked and wx.ART_UNLOCK or wx.ART_LOCK),
                                    size=wx.Size(16, 16))
                self.controls['lock'] = w
                szr.Add(w, 0)
                w.Bind(wx.EVT_LEFT_UP, lambda e: self.__toggle_lock())
            if 'eye' in controls:
                
                w = wx.StaticBitmap(wnd, -1, wx.ArtProvider.GetBitmap(wx.ART_SHOW),
                                    size=wx.Size(16, 16))
                self.controls['eye'] = w
                szr.Add(w, 0)
            szr.Fit(wnd)
        
        if None == parent:
            self.tree.DeleteAllItems()
            self.item = self.tree.AddRoot(self.name, image=self.bitmap_id(self.art), wnd=wnd)
        else:
            self.item = self.tree.AppendItem(self.parent.item, self.name,
                                             image=self.bitmap_id(self.art), wnd=wnd)
        self.tree.SetPyData(self.item, weakref.proxy(self))
        
        self.create_panel(getattr(self, 'panel_description', []))
        
        if getattr(self, 'item_is_visible', False): self.tree.EnsureVisible(self.item)
        if getattr(self, 'item_is_expanded', False): self.tree.Expand(self.item)
        self.is_selected = getattr(self, 'item_is_selected', False)
        if self.is_selected: self.tree.SelectItem(self.item)
        
    def __toggle_lock(self):
        self.tree.SelectItem(self.item)
        self.lock(not self.is_locked)
            
    def lock(self, really_lock):
        self.is_locked = really_lock
        try:
            self.controls['lock'].SetBitmap(wx.ArtProvider.GetBitmap(
                self.is_locked and wx.ART_UNLOCK or wx.ART_LOCK))
        except: pass
    
    def create_panel(self, description):
        self.panel = Panel(self, *(description or ('EMPTY_PROPS', {})))
    
    def __getstate__(self):
        ''' Helper function to get objects to be saved in history '''
        volatile_objects = ['tree', 'parent', 'item', 'panel', 'controls'] + \
                           getattr(self, 'volatile_objects', [])
        
        self.item_is_visible = self.tree.IsVisible(self.item)
        self.item_is_expanded = self.tree.IsExpanded(self.item)
        self.item_is_selected = self.tree.IsSelected(self.item)
        return dict([(k, v) for k, v in self.__dict__.iteritems() \
                         if k not in volatile_objects])
    
    def track(self):
        ''' Record current state in history '''
        EditorGlobals.browser_window.track()
    
    def bitmap_id(self, art_id):
        ''' Get bitmap by id '''
        return Lib.Editor.Commons.ArtProvider.GetBitmapId(art_id)
    
    def guess_name(self, dictionary, name):
        ''' Guess name for new object in dictionary, starting
            with `name` prefix. '''
        name = self.toidentifier(name)
        if name and not dictionary.has_key(name): return name
        i = 1
        while True:
            guessed_name = (name + '_' + str(i))
            if not dictionary.has_key(guessed_name): break
            i += 1
        return guessed_name
    
    def rename(self):
        ''' Rename relf '''
        new_name = EditorGlobals.browser_window.rename_dialog(self.name, 
                                                               self._check_correct_name)
        if not new_name: return
        self.track()
        if self.parent:
            self.parent.children.change_key(self.name, new_name)
            if hasattr(self.parent, 'get_object'):
                self.parent.get_object().objects.change_key(self.name, new_name)
        self.name = new_name
        self.tree.SetItemText(self.item, self.name)
    
    def _check_correct_name(self, name):
        for l in name:
            if ord(l) > 128: return None
        name = self.toidentifier(name)
        if name and self.parent and (name != self.name and self.parent.children.has_key(name)):
            return None
        return name
    
    def yesno_dialog(self, text):
        ''' Display yes-no dialog '''
        return EditorGlobals.browser_window.yesno_dialog(text)
    
    def fileopen_dialog(self, wildcard, style, working_dir=os.getcwd()):
        '''
        Display file open/save dialog.
        Returns relative path on success, None on abort/failure.
        '''
        return EditorGlobals.browser_window.fileopen_dialog(wildcard, style, working_dir)
    
    def to_relative_path(self, path):
        '''
        Convert path to relative path (starting from .exe file directory)
        Returns None if path is outside editor directory.
        '''
        return EditorGlobals.browser_window.to_relative_path(path)
    
    def hash(self, string):
        ''' Get hash for string '''
        file_hash = dir_h = 5381
        for c in string: file_hash = ((file_hash << 5) + file_hash) + ord(c)
        return file_hash & 0xFFFFFFFF
    
    def get_location_position(self):
        l = EditorGlobals.browser_window.loaded_location.location
        return Tanita2.vec2(l.position)
    
    def get_screen_center(self):
        ''' Get absolute coordinates of screen center '''
        l = EditorGlobals.browser_window.loaded_location.location
        return [-l.position.x + 512 / Globals.zoom, 
                -l.position.y + 384 / Globals.zoom]
    
    def _update_item_order(self):
        EditorGlobals.browser_window._update_item_order()
                
    def escape(self, name):
        ''' Escape special symbols in string '''
        return name.replace('\\', '\\\\').replace("'", "\\'")
    
    def toidentifier(self, name):
        n = ''
        first = True
        for c in name:
            if ' ' == c: first = True
            if ('_' == c or c.isalnum()) and (not first or c.isalpha()):
                n += (first and c.upper() or c.lower())
                first = False
        return n

    def on_begin_drag(self):
        return True
    
    def on_end_drag(self, over_object, sibling_classes=[], extended=False):
        sibling_classes.append(self.__class__)
        
        from Path import Path
        from Point import Point
        from Layer import Layer
        from AnimatedObject import AnimatedObject
        from StaticImage import StaticImage
        from LocationSeparator import LocationSeparator
        from Sound import Sound
        from Separator import Separator

        if (self.__class__ is LocationSeparator):
            di = 1
            if self.parent.children.get_index(over_object.name) < \
               self.parent.children.get_index(self.name): di = 0
            
            if self.parent.children.get_index(self.name) == \
               self.parent.children.get_index(over_object.name)+di: return False
            self.track()
            del self.parent.children[self.name]
            self.parent.children.insert(
                self.parent.children.get_index(over_object.name)+di,
                self.name, self)
            return True


        if extended or self.__class__ is StaticImage:
            if over_object.__class__ is Layer and over_object is not self.parent:
                self.track()
                
                del self.parent.children[self.name]
                new_name = over_object.guess_name(over_object.children, self.name)
                over_object.children.insert(0, new_name, self)
                
                self.name = new_name
                self.tree.SetItemText(self.item, self.name)
                
                abspos = self.get_object().absolute_position - self.get_location_position()
                self.set_position([abspos.x, abspos.y])
                return True

        if self.__class__ is Sound:
            if over_object.__class__ is AnimatedObject and over_object is not self.parent:
                self.track()
                
                del self.parent.children[self.name]
                new_name = over_object.guess_name(over_object.children, self.name)
                index = 0
                for c in over_object.children.itervalues():
                    if c.__class__ is Separator and c.id == over_object.id_sequences: break
                    index += 1
                over_object.children.insert(index, new_name, self)
                
                self.name = new_name
                self.tree.SetItemText(self.item, self.name)
                
                abspos = self.get_object().absolute_position - self.get_location_position()
                self.set_position([abspos.x, abspos.y])
                return True
        
        if extended or self.__class__ is Path or self.__class__ is Point:
            if over_object.__class__ is Layer and over_object is not self.parent:
                self.track()
                
                del self.parent.children[self.name]
                new_name = over_object.guess_name(over_object.children, self.name)
                over_object.children.insert(0, new_name, self)
                
                self.name = new_name
                self.tree.SetItemText(self.item, self.name)
                
                abspos = self.get_object().absolute_position - self.get_location_position()
                self.set_position([abspos.x, abspos.y])
                return True
        
        if extended and not self.__class__ is Path and not self.__class__ is Point:
            if over_object.parent and over_object.parent.__class__ is AnimatedObject and \
               over_object.parent is not self.parent:
                p = over_object.parent
                import weakref
                while p:
                    if p is weakref.proxy(self): return False
                    p = p.parent
                
                old_pos = self.parent.get_object().absolute_position
                
                over_object = over_object.parent
                
                del self.parent.children[self.name]
                new_name = over_object.guess_name(over_object.children, self.name)
                
                index = 0
                for c in over_object.children.itervalues():
                    if c.__class__ in sibling_classes: break
                    index += 1
                    
                over_object.children.insert(index, new_name, self)
                
                self.name = new_name
                self.tree.SetItemText(self.item, self.name)
                
                new_pos = over_object.get_object().absolute_position
                pos = self._get_pos_object()
                pos[0] += -new_pos.x + old_pos.x
                pos[1] += -new_pos.y + old_pos.y
                return True
        
        if over_object is self.parent:
            if self.parent.children.get_index(self.name) == 0: return False
            
            self.track()
            del self.parent.children[self.name]
            
            index = 0
            if extended:
                for c in over_object.children.itervalues():
                    if c.__class__ in sibling_classes: break
                    index += 1
            self.parent.children.insert(index, self.name, self)
            return True

        if (self.parent.__class__ is Layer or \
            over_object.__class__ in sibling_classes) and \
           self in over_object.parent.children.itervalues():
            di = 1
            if self.parent.children.get_index(over_object.name) < \
               self.parent.children.get_index(self.name): di = 0
            
            if self.parent.children.get_index(self.name) == \
               self.parent.children.get_index(over_object.name)+di: return False
            self.track()
            del self.parent.children[self.name]
            self.parent.children.insert(
                self.parent.children.get_index(over_object.name)+di,
                self.name, self)
            return True
        return False


class OrderedDict:
    ''' Class for dictionary object with fixed order of elements '''
    
    def __init__(self): self.dictionary = []
    def __setitem__(self, name, item): self.dictionary.append((name, item))
    def __getitem__(self, name):
        for k, v in self.dictionary:
            if name == k: return v
        raise KeyError, 'Key not found: "%s"' % name
    def __delitem__(self, name):
        for i in xrange(len(self.dictionary)):
            if self.dictionary[i][0] == name: del self.dictionary[i]; return
        raise KeyError, 'Key not found: "%s"' % name
    def has_key(self, key):
        for k, v in self.dictionary:
            if key == k: return True
        return False
    def keys(self): return [k for k, v in self.dictionary]
    def clear(self): self.dictionary = []
    def itervalues(self): return [v for k, v in self.dictionary]
    def iteritems(self): return self.dictionary[:]
    def iterkeys(self): return self.keys()
    def change_key(self, old_key, new_key):
        assert old_key == new_key or not self.has_key(new_key), 'Key already exists'
        for i in xrange(len(self.dictionary)):
            if self.dictionary[i][0] == old_key:
                self.dictionary[i] = (new_key, self.dictionary[i][1])
                return
        raise KeyError, 'Key not found: "%s"' % old_key
    def insert(self, index, key, value):
        assert not self.has_key(key), 'Key already exists'
        self.dictionary.insert(index, (key, value))
    def get_index(self, key):
        for i in xrange(len(self.dictionary)):
            if self.dictionary[i][0] == key: return i
        raise KeyError, 'Key not found: "%s"' % key
    def __str__(self): return str(self.dictionary)
    def __len__(self): return len(self.dictionary)
    def swap(self, i1, i2):
        self.dictionary[i1], self.dictionary[i2] = self.dictionary[i2], self.dictionary[i1]

class PositionDialog:
    def __init__(self):
        self.dialog = EditorGlobals.browser_window.load_dialog(Lib.parent_window, 'POSITION_DLG')
        self.x_edit = self.dialog.FindWindowByName('POSITION_X')
        self.x_edit.Bind(wx.EVT_TEXT_ENTER, lambda e: self.hide())
        self.x_edit.Bind(wx.EVT_KEY_DOWN, self.__on_esc)
        
        self.y_edit = self.dialog.FindWindowByName('POSITION_Y')
        self.y_edit.Bind(wx.EVT_TEXT_ENTER, lambda e: self.hide())
        self.y_edit.Bind(wx.EVT_KEY_DOWN, self.__on_esc)
        self.dialog.Bind(wx.EVT_ACTIVATE, self.__on_activate)
        wx.EVT_CLOSE(self.dialog, lambda e: self.hide())
        self.dialog.Move((config["x"] + 5, config["y"] + 20))
        
    def __on_esc(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE: self.hide()
        event.Skip()
        
    def __on_activate(self, event):
        if not event.GetActive(): self.hide()
    
    def is_shown(self): return self.dialog.IsShown()
    def show(self, element):
        self.dialog.Show()
        Tanita2.disable_autoactivation(True)
        self.dialog.Move((config["x"], config["y"] + 20))
        self.element = element
        
        element_pos = element.get_position()
        self.x_edit.SetValue(str(int(element_pos[0])))
        self.y_edit.SetValue(str(int(element_pos[1])))
                
    def hide(self):
        self.dialog.Hide()
        Tanita2.disable_autoactivation(False)
        
        try: self.element.__dict__
        except:
            self.element = None
            return
        
        new_pos = self.element.get_position()
        try: new_pos[0] = float(int(self.x_edit.GetValue()))
        except ValueError: pass
        try: new_pos[1] = float(int(self.y_edit.GetValue()))
        except ValueError: pass
        
        if new_pos == self.element.get_position(): return
        self.element.track()
        self.element.set_position(new_pos)
        self.element = None

class Panel:
    ''' Properties panel '''
    def __init__(self, parent, panel_id, controls):
        self.window = EditorGlobals.property_window.load_panel(panel_id)
        self.parent = weakref.proxy(parent)
        for name, window_name in controls.iteritems():
            assert not self.__dict__.has_key(name), 'Setting attribute that was already set'
            setattr(self, name, self.window.FindWindowByName(window_name))
            assert getattr(self, name, None), 'Control "%s" not found' % window_name
            
    def show(self):
        getattr(self.parent, 'on_panel_show', lambda: None)()
        self.window.Show()
    
    def hide(self):
        getattr(self.parent, 'on_panel_hide', lambda: None)()
        self.window.Hide()
