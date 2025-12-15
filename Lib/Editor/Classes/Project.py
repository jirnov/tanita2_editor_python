'''
Project tree element
'''
import wx
from Lib.Editor import EditorGlobals
from Misc import ItemBase
from Location import Location
from LocationSeparator import LocationSeparator
from weakref import proxy

class Project(ItemBase):
    ''' Project (tree root) '''
    
    def __init__(self, name):
        self.startup_location = ''
        self.panel_description = ['PROJECT_PROPS', {'locs' : 'LOCATIONS',}]
        ItemBase.__init__(self, name, None, wx.ART_PROJECT)
    
    def __setstate__(self, state):
        self.__dict__ = state.copy()
        self.create_volatile_objects(None)
        
        def create_volatile_objects(obj):
            try:
                for n, c in obj.children.iteritems():
                    c.create_volatile_objects(obj)
                    create_volatile_objects(proxy(c))
            except: print obj; raise
        create_volatile_objects(proxy(self))
        
    def create_volatile_objects(self, parent, controls=[]):
        ItemBase.create_volatile_objects(self, parent, controls)
        
    def save(self):
        ''' Save project information '''
        def get_name(child, name):
            name = self.escape(name)
            if child.__class__ is LocationSeparator:
                return '-- %s --' % name
            return name

        j = file('World/junctions.txt', 'wt')
        j.write(
'''# This file is generated automatically.
# Please don't edit it by hand because your
# changes will be rewritten by editor.

# short project name
project = '%s'

# startup location
startup_location = '%s'

# junctions table
locations = [
    %s
]''' % (self.escape(self.name), self.escape(self.startup_location),
        ',\n    '.join(['"%s"' % get_name(v, n) for n, v in self.children.iteritems()])))
        j.close()
    
    def on_menu(self, event):
        return [('New location', wx.ART_LOCATION, self.__on_new_location),
                ('New separator', wx.ART_EMPTY, self.__on_new_separator),
                (None),
                ('Rename')]

    def __on_new_separator(self, event):
        new_name = EditorGlobals.browser_window.rename_dialog(
            self.guess_name(self.children, 'Separator'), self._check_correct_name,
            caption='Separator name')
        new_name = '(' + new_name + ')'
        self.children[new_name] = LocationSeparator(new_name, self)
        self.tree.SelectItem(self.children[new_name].item)

    
    def __on_new_location(self, event):
        new_name = EditorGlobals.browser_window.rename_dialog(
            self.guess_name(self.children, 'Location'), self._check_correct_name,
            caption='Location name')
        if not new_name: return
        self.track()
        self.children[new_name] = Location(new_name, self)
        self.tree.SelectItem(self.children[new_name].item)
        if not EditorGlobals.browser_window.loaded_location:
            self.children[new_name].load()
            
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_COMBOBOX, lambda e: self.on_panel_hide())
        self.panel.locs.Clear()
        
        sel_i = -1
        index = 0
        for z in self.children.itervalues():
            i = z.name
            if i == self.startup_location:
                sel_i = index
            if z.__class__ == Location:
                self.panel.locs.Append(i)
                index += 1
        
        if -1 != sel_i: self.panel.locs.Select(sel_i)
        else:
            if 0 == len(self.children):
                self.panel.locs.Disable()
            else:
                self.panel.locs.Enable()
                self.startup_location = self.children.keys()[0][:]
                self.panel.locs.Select(0)
    
    def on_panel_hide(self):
        if 0 == len(self.children): return
        sel = self.panel.locs.GetSelection()
        if wx.NOT_FOUND == sel: return
        
        self.startup_location = self.panel.locs.GetString(sel)
    
    def check(self):
        if self.startup_location not in self.children.iterkeys():
            return 'Project: starting location is invalid'
    
    def check_all(self):
        messages = []
        def check(o):
            if not hasattr(o, 'check'):
                msg = '%s doesn\'t have check() method' % o.__class__
            else: msg = o.check()
            if msg: messages.append(msg)
            
            for l in o.children.itervalues():
                check(l)
        check(self)
        if messages:
            EditorGlobals.browser_window.assert_dialog(messages)
            return False
        return True
        
    def export(self, path='World'):
        # Saving "junctions.txt"
        self.save()
        
        # Checking correctness
        if not self.check_all(): return
        
        # Saving locations
        for l in self.children.itervalues():
            if not l.loaded: continue

            if hasattr(l, 'export'):            
                l.export(path)
                import Tanita2
                Tanita2.disable_autoactivation(True)
                wx.MessageBox('Location "%s" successfully exported' % l.name,
                              'Information')
                Tanita2.disable_autoactivation(False)

    def on_cleanup(self):
        self.save()
