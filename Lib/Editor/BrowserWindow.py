"""
Module implementing location tree browser
"""
import wx, gc, Commons, Lib.Globals, Classes, EditorGlobals
import os, os.path
from Lib import debug, config
import wx.lib.customtreectrl as customtree
from weakref import proxy

class BrowserWindow(Commons.EditorWindowBase):
    def __init__(self, parent):
        # Creating window
        super(BrowserWindow, self).__init__(parent, -1, "Objects Tree", (0, 0), 
                                            (config["x"], config["actual_height"]))
        self.history = []
        self.history_mark = 0
        
        # Creating widgets
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.__create_toolbar()
        self.__create_tree()
        
        # Loading location list
        self.loaded_location = None
        self.__load_location_list()
        
        # Misc
        self.Bind(wx.EVT_CLOSE, lambda event: False) # Ignoring close event
        self.SetSizer(self.sizer)
        self.Layout()
        self.Show(True)
        
        # Rename dialog
        self.__rename_dialog = self.load_dialog(parent, 'RENAME_DLG')
        self.__rename_dialog_edit = self.__rename_dialog.FindWindowByName('NEWNAME')
        wnd = self.__rename_dialog.FindWindowByName('wxID_OK')
        assert self.__rename_dialog_edit and wnd, 'Invalid control'
        self.__rename_dialog.Bind(wx.EVT_BUTTON, self.__on_rename_yes_btn, wnd)
        
        # Export assertions dialog
        self.__assert_dialog = self.load_dialog(parent, 'EXPORT_DLG')
        self.__assert_dialog_list = self.__assert_dialog.FindWindowByName('ERRORS')
        #wnd = self.__rename_dialog.FindWindowByName('wxID_OK')
        assert self.__assert_dialog_list, 'Invalid control'
        #self.__rename_dialog.Bind(wx.EVT_BUTTON, self.__on_rename_yes_btn, wnd)
        
        # Debug message
        debug("BrowserWindow created")
        
    # Parse junctions.txt and build location list
    def __load_location_list(self):
        contents = {}
        if not os.path.exists('World/junctions.txt'):
            debug('junctions.txt file not found. Creating new.')
            file('World/junctions.txt', 'wt').write(
'''project = 'Please enter project name'
startup_location = ''
junctions = []
''')
        exec file('World/junctions.txt', 'rt') in {}, contents
        
        self.startup_location = contents['startup_location']
        locations = contents['locations']
    
        # Adding tree items for locations
        self.project = Classes.Project(contents['project'])
        self.project.startup_location = self.startup_location[:]
        for location in locations:
            if location.startswith('-- '):
                location = location[3:-3]
                self.project.children[location] = Classes.LocationSeparator(location, self.project)
            else:
                self.project.children[location] = Classes.Location(location, self.project)
        self.tree.Expand(self.project.item)
        self.tree.SelectItem(self.project.item)
        EditorGlobals.property_window.set_panel(self.project.panel)
        
    # Create toolbar
    def __create_toolbar(self):
        self.toolbar = Commons.ToolBar(self)
        self.sizer.Add(self.toolbar, 0, wx.EXPAND | wx.FIXED_MINSIZE)
        
        self.save_tool = id = self.toolbar.AddTool(wx.ART_FILE_SAVE)
        self.toolbar.EnableTool(id, False)
        self.Bind(wx.EVT_TOOL, self.__on_save, id=id)
        
        self.toolbar.AddSeparator()
        
        id = self.toolbar.AddTool(wx.ART_ZOOM_IN)
        self.Bind(wx.EVT_TOOL, lambda e: self.__set_zoom(Lib.Globals.zoom * 1.2), id=id)
        
        id = self.toolbar.AddTool(wx.ART_ZOOM_RESET)
        self.Bind(wx.EVT_TOOL, lambda e: self.__set_zoom(1.0), id=id)
        
        id = self.toolbar.AddTool(wx.ART_ZOOM_OUT)
        self.Bind(wx.EVT_TOOL, lambda e: self.__set_zoom(Lib.Globals.zoom / 1.2), id=id)
        
        self.toolbar.AddSeparator()
        
        self.undo_tool = id = self.toolbar.AddTool(wx.ART_UNDO)
        self.toolbar.EnableTool(id, False)
        self.Bind(wx.EVT_TOOL, self.__on_undo, id=id)
        
        self.redo_tool = id = self.toolbar.AddTool(wx.ART_REDO)
        self.toolbar.EnableTool(id, False)
        self.Bind(wx.EVT_TOOL, self.__on_redo, id=id)
        
        self.toolbar.AddSeparator()
        
        self.lock_tool = id = self.toolbar.AddTool(wx.ART_LOCK_ALL)
        self.Bind(wx.EVT_TOOL, self.__on_lock_all, id=id)
        
        self.toolbar.AddSeparator()
        
        self.check_tool = id = self.toolbar.AddTool(wx.ART_CHECK)
        self.toolbar.EnableTool(id, False)
        self.Bind(wx.EVT_TOOL, self.__on_check, id=id)
        
        self.toolbar.AddSeparator()

        self.export_tool = id = self.toolbar.AddTool(wx.ART_EXPORT)
        self.toolbar.EnableTool(id, False)
        self.Bind(wx.EVT_TOOL, lambda e: self.project.export(), id=id)
    
    # Save current location
    def __on_save(self, event):
        if self.loaded_location: 
            self.loaded_location.save()
    
    # Set zoom factor
    def __set_zoom(self, zoom): Lib.Globals.zoom = zoom
    
    # Undo last changes
    def __on_undo(self, event):
        if len(self.history) == self.history_mark:
            self.track()
            self.history_mark -= 1
        
        self.history_mark -= 1
        self.toolbar.EnableTool(self.redo_tool, True)
        if 0 == self.history_mark: self.toolbar.EnableTool(self.undo_tool, False)
        
        assert self.history_mark >= 0, "Illegal undo history index"
        self.__common_do()
        
    # Redo last changes
    def __on_redo(self, event):
        self.history_mark += 1
        
        self.toolbar.EnableTool(self.undo_tool, True)
        if len(self.history) - 1 == self.history_mark:
            self.toolbar.EnableTool(self.redo_tool, False)
        
        assert self.history_mark < len(self.history), "Illegal undo history index"
        self.__common_do()
        
    # Common code for undo/redo
    def __common_do(self):
        self.tree.Freeze()
        self.tree.Collapse(self.tree.GetRootItem())
        EditorGlobals.property_window.Freeze()
        Lib.parent_window.SetCursor(wx.HOURGLASS_CURSOR)

        if self.loaded_location: self.loaded_location.unload()
        del self.project
        gc.collect()
        
        import cPickle
        self.project = cPickle.loads(self.history[self.history_mark])
        
        try: self.loaded_location.__dict__
        except: self.loaded_location = None
        
        EditorGlobals.property_window.Thaw()
        self.tree.Thaw()
        Lib.parent_window.SetCursor(wx.STANDARD_CURSOR)
        
    # Lock all objects
    def __on_lock_all(self, event):
        if self.loaded_location:
            def lock_all(parent):
                parent.lock(True)
                for c in parent.children.itervalues():
                    lock_all(c)
            lock_all(self.loaded_location)
    
    def __on_check(self, event):
        if self.project.check_all():
            wx.MessageBox('Location check succeeded!', 'Check passed',
                          wx.OK | wx.CENTER | wx.ICON_INFORMATION)
    
    # Create tree view
    def __create_tree(self):
        self.tree = customtree.CustomTreeCtrl(self, ctstyle=wx.TR_HAS_BUTTONS |
                                              wx.TR_HAS_VARIABLE_ROW_HEIGHT |
                                              wx.TR_SINGLE)
        self.sizer.Add(self.tree, 1, wx.EXPAND)
        self.tree.AssignImageList(Commons.ArtProvider.image_list)
        
        self.tree.Bind(wx.EVT_TREE_ITEM_MENU, self.__on_tree_item_menu)
        self.tree.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.__on_item_expanding)
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.__on_tree_item_click)
        self.tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.__on_begin_drag)
        self.tree.Bind(wx.EVT_TREE_END_DRAG, self.__on_end_drag)
    
    # Show tree item context menu
    def __on_tree_item_menu(self, event):
        elm = self.__get_event_object(event)
        if not elm: return
        
        # Getting menu description
        on_menu = getattr(elm, "on_menu", None)
        if not on_menu: return
        descr = on_menu(event)
        if not descr: return
        
        # Creating menu
        menu = wx.Menu()
        
        # Adding items
        for item in descr:
            if None == item or (None,) == item: menu.AppendSeparator(); continue
            if ('Rename') == item:
                item = ('Rename', wx.ART_RENAME, lambda e: elm.rename())
            name, art_id, handler = item
            id = wx.NewId()
            item = wx.MenuItem(menu, id, name)
            item.SetBitmap(wx.ArtProvider.GetBitmap(art_id))
            menu.AppendItem(item)
            if handler: self.Bind(wx.EVT_MENU, handler, id=id)

        # Showing menu
        self.tree.PopupMenu(menu)
        menu.Destroy()
    
    # Tree item selection
    def __on_tree_item_click(self, event):
        # Deselecting all items
        def deselect(i):
            for a in i.children.itervalues(): deselect(a)
            i.is_selected = False
        if self.loaded_location: deselect(self.loaded_location)
        
        # Switching panel
        elm = self.__get_event_object(event)
        if not elm: return
        elm.is_selected = True
        if EditorGlobals:
            EditorGlobals.property_window.set_panel(elm.panel)
    
    # Tree item is being expanded
    def __on_item_expanding(self, event):
        elm = self.__get_event_object(event)
        if elm and not getattr(elm, 'is_visible', True): event.Veto()
        
    # Tree item dragging start
    def __on_begin_drag(self, event):
        elm = self.__get_event_object(event)
        if elm and getattr(elm, 'on_begin_drag', False) and \
           elm.on_begin_drag():
            event.Allow()
            self.item_to_drag = elm
    
    # Tree item dragging end
    def __on_end_drag(self, event):
        elm = self.__get_event_object(event)
        if self.item_to_drag and elm and elm is not self.item_to_drag and \
           getattr(self.item_to_drag, 'on_end_drag', False) and \
           self.item_to_drag.on_end_drag(elm):
            self._update_item_order()
        self.item_to_drag = None
        
    def _update_item_order(self):
        elm = self.__get_selected_object(None)
        self.track()
        self.history_mark -= 1
        self.__common_do()
    
    # Helper function to return event item object or None
    def __get_event_object(self, event):
        item = event.GetItem()
        if not item or not item.IsOk(): return None
        obj = self.tree.GetPyData(item)
        if not obj: return None
        return obj
    
    # Helper function to return selected item object or None
    def __get_selected_object(self, event):
        item = self.tree.GetSelection()
        if not item or not item.IsOk(): return None
        obj = self.tree.GetPyData(item)
        if not obj: return None
        return obj
    
    # Unload all other locations. Returns True if we can continue location load
    def prepare_location_load(self):
        if self.loaded_location and \
           wx.ID_YES != self.yesno_dialog('Are you sure?'): return False
        
        for location in self.project.children.itervalues():
            location.unload()
        self.clear_history()
        gc.collect()
        
        self.toolbar.EnableTool(self.export_tool, config.has_key('expert_mode') and config['expert_mode'])
        self.toolbar.EnableTool(self.save_tool, True)
        self.toolbar.EnableTool(self.check_tool, True)
        return True
    
    # Show rename dialog and return new name or None
    def rename_dialog(self, old_name, on_name_guess, caption='Rename'):
        import Tanita2
        assert on_name_guess, 'Invalid rename handler'
        self.__rename_on_name_guess = proxy(on_name_guess)
        self.__rename_dialog.SetTitle(caption)
        
        # Setting old name text
        self.__rename_dialog_edit.SetValue(old_name)
        self.__rename_dialog_edit.SetSelection(-1, -1)
        self.__rename_dialog_edit.SetFocus()
        
        # Showing dialog
        Tanita2.disable_autoactivation(True)
        retcode = self.__rename_dialog.ShowModal()
        Tanita2.disable_autoactivation(False)
        if wx.ID_OK == retcode and self.__rename_new_name:
            return self.__rename_new_name
        return None
    
    def __on_rename_yes_btn(self, event):
        self.__rename_new_name = None
        new_name = self.__rename_dialog_edit.GetValue()
        
        if new_name: new_name = self.__rename_on_name_guess(new_name)
        if not new_name:
            wx.MessageBox('This name is either invalid or already in use.\n' + \
                          'Please check if name contains cyrillic symbols',
                          caption='Invalid name', parent=self.__rename_dialog)
        else:
            self.__rename_new_name = new_name
            event.Skip()

    # Save current state to history
    def track(self):
        if len(self.history) > 100: self.history = self.history[-100:]
        self.history = self.history[:self.history_mark]
        import cPickle
        self.history.append(cPickle.dumps(self.project, -1))
        self.history_mark = len(self.history)
        
        self.toolbar.EnableTool(self.undo_tool, True)
        
    # Clear history
    def clear_history(self):
        self.history = []
        self.history_mark = 0
        self.toolbar.EnableTool(self.undo_tool, False)
        self.toolbar.EnableTool(self.redo_tool, False)
        
    def assert_dialog(self, messages):
        self.__assert_dialog.SetSize(wx.Size(400, 500))
        self.__assert_dialog_list.Clear()
        self.__assert_dialog_list.InsertItems(messages, 0)
        self.__assert_dialog.ShowModal()

    def on_frame(self, dt):
        if self.loaded_location:
            self.loaded_location.draw(dt)

    def on_move_request(self, x_direction, y_direction, shift_pressed):
        if self.loaded_location:
            self.loaded_location.on_move_request(x_direction, y_direction, shift_pressed)

    def on_cleanup(self):
        if self.loaded_location:
            self.loaded_location.on_cleanup()
        if self.project:
            self.project.on_cleanup()
        self.Destroy()
