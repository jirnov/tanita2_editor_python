"""
Module implementing object properties window
"""
import wx, Commons, Lib.Globals, EditorGlobals
from Lib import debug, config
from weakref import proxy

class PropertyWindow(Commons.EditorWindowBase):
    def __init__(self, parent):
        # Creating window
        super(PropertyWindow, self).__init__(parent, -1, "Properties", 
                                             (0, config["actual_height"]), 
                                             (config["x"] + config["actual_width"], 200))
        self.Bind(wx.EVT_CLOSE, lambda event: False) # Ignoring close event
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        
        self.SetAutoLayout(True)
        self.Show(True)
        self.panel_object = None
        
        if getattr(Lib.Globals, 'panels', False):
            for p in Lib.Globals.panels.itervalues(): p.Destroy()
        Lib.Globals.panels = {}
        
        # Debug message
        debug("PropertyWindow created")
        
    def load_panel(self, panel_id):
        ''' Load panel from resource '''
        if Lib.Globals.panels.has_key(panel_id):
            return Lib.Globals.panels[panel_id]
        panel = EditorGlobals.browser_window.resource.LoadPanel(self, panel_id)
        if not panel: raise IOError("'%s' resource not found" % panel_id)
        panel.Hide()
        Lib.Globals.panels[panel_id] = panel
        return panel
    
    def set_panel(self, panel):
        ''' Change panel '''

        # Removing old panel
        self.Freeze()
        try: prev = self.sizer.GetItem(0)
        except: pass
        else:
            prev = prev.GetWindow()
            if not prev: self.Thaw(); return
            
            self.sizer.Detach(0)
            try: dir(self.panel_object)
            except: pass
            else:
                if hasattr(self.panel_object, 'Hide'):
                    self.panel_object.Hide()
                else: self.panel_object.hide()
        
        # Adding new panel
        assert panel and panel.window, 'Attempt to set invalid panel'
        self.sizer.Add(panel.window, 1, wx.EXPAND)
        self.panel_object = proxy(panel)
        panel.show()
        self.Layout()
        self.Thaw()

    def on_cleanup(self):
        self.Destroy()
