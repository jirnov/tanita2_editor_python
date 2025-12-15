"""
Common declarations for both engine modes.
"""
import sys, traceback, Lib, Globals, Tanita2
# Functions used in release mode
# They are overloaded in debug mode

def catch( func, *args, **kwargs ):
    '''
    Call function with exception handling.
    '''
    return func(*args, **kwargs)

def display_traceback():
    '''
    Display exception traceback.
    \return always 0.
    '''
    tb_message = traceback.format_exc()
    sys.stderr.traceback(tb_message)
    return 0

def reload_modules():
    '''
    Reload all modules
    '''
    return

def on_init( parent_hwnd ):
    '''
    Module initializations
    '''
    return

def on_frame( dt, just_redraw, cursor_position, mouse_buttons ):
    '''
    Module update on each frame.
    \return true if update succeeded
    '''
    if Lib.config['left_handed_mouse']:
        bit1 = (mouse_buttons & 1)
        bit2 = (mouse_buttons & 2) >> 1
        mouse_buttons = mouse_buttons & 0xFC | (bit1 << 1) | bit2
    Globals.mouse_buttons = mouse_buttons
    Globals.mouse_position = cursor_position
    Globals.cursor_position = cursor_position
        
    #Globals.cursor_position = cursor_position - Globals.location.position
    #Globals.cursor_position = vec2(min((cursor_position - Globals.location.position).x , Lib.config['width']), \
    #                                min((cursor_position - Globals.location.position).y , Lib.config['height']))
    return not just_redraw

def on_cleanup():
    '''
    Deinitializations
    '''
    return

# Debug mode overloads

if Lib.config["debug"]:
    # Theese modules will not be reloaded
    import Tanita2, __builtin__, gc, wx, wx.xrc as xrc, wx.lib.customtreectrl
    import wx.py.crust
    
    # Class for keeping track of imported module
    class RollbackImporter:
        def __init__(self):
            self.__previous = sys.modules.copy()
            self.__old_import = __builtin__.__import__
            __builtin__.__import__ = self._import
            self.__modules = {}
            return
        
        # Import function hook
        def _import(self, name, globals=None, locals=None, fromlist=[]):
            result = self.__old_import(name, globals, locals, fromlist)
            if not self.__modules.has_key(result.__name__):
                self.__modules[result.__name__] = True
            return result
            
        # Module reloading
        def reload(self):
            for modname in self.__modules.keys()[:]:
                if not self.__previous.has_key(modname):
                    try: del(sys.modules[modname])
                    except: del self.__modules[modname]
            gc.collect()
            return
    
    # Setting rollback module importer for
    # modules being loaded after this declaration
    global rollback_importer
    rollback_importer = RollbackImporter()
    
    class TracebackDialog:
        '''
        Traceback dialog class.
        '''
        # ShowModal return values
        TB_BREAK = 0   # Break program execution
        TB_IGNORE = 1  # Ignore exception
        TB_RETRY = 2   # Reload and retry
        
        def __init__(self, resource_path):
            '''
            Loading dialog from resource
            \param  resource_path  path to file with xrc 
                                   resource to load dialog from
            '''
            # Opening resource
            res = xrc.XmlResource(resource_path)
            assert res, "Missing or invalid resource file"
            # Loading dialog
            global parent_window
            self.dlg = res.LoadDialog(parent_window, "TRACEBACK_DLG")
            assert self.dlg, "'TRACEBACK_DLG' resource not found"
            # Finding text control
            self.text_ctrl = self.dlg.FindWindowByName("TRACEBACK_TEXT")
            assert self.text_ctrl, "'TRACEBACK_TEXT' control not found"
            # Finding buttons
            self.btn_break = self.dlg.FindWindowByName("BREAK_BTN").GetId()
            self.btn_ignore = self.dlg.FindWindowByName("IGNORE_BTN").GetId()
            self.btn_retry = self.dlg.FindWindowByName("RETRY_BTN").GetId()
            
            # Binding button events
            wx.EVT_BUTTON(self.dlg, self.btn_break, self.__on_click)
            wx.EVT_BUTTON(self.dlg, self.btn_ignore, self.__on_click)
            wx.EVT_BUTTON(self.dlg, self.btn_retry, self.__on_click)
            wx.EVT_CLOSE(self.dlg, self.__on_click)
            return

        def ShowModal(self, traceback_text):
            '''
            Show traceback dialog
            \param  traceback_text  traceback string to display
            '''
            self.text_ctrl.SetValue(traceback_text)
            return self.dlg.ShowModal()
        
        # Button click management
        def __on_click(self, event):
            retcode = self.TB_BREAK
            if event.GetId() == self.btn_ignore: retcode = self.TB_IGNORE
            if event.GetId() == self.btn_retry: retcode = self.TB_RETRY
            self.dlg.EndModal(retcode)
            return
        
    class MyApplication(wx.App):
        """
        wxWidgets application class.
        """
        def __init__(self):
            class mylog(Tanita2._PythonLogger):
                buffer = ""
                def write(self, text):
                    '''
                    Write text to log file
                    '''
                    self.buffer += text
                    Tanita2._PythonLogger.write_error(self, text)
                    return
                # Dummy method for wxWidgets use
                def SetParent(self, parent): pass
                
                # Flush error log
                def flush(self):
                    if self.buffer:
                        Tanita2._PythonLogger.traceback(self, self.buffer)
                        self.buffer = ""
                    return
            
            redirect = False
            if Lib.config["use_wx_log"]:
                redirect = True
                self.outputWindowClass = mylog
            wx.App.__init__(self, redirect=redirect)
            return
    
    # wxWidgets application
    global wxapplication
    wxapplication = None
    
    # Reload all modules tracked by RollbackImporter
    def debug_reload_modules():
        import Tanita2
        Tanita2.on_script_reload()
        rollback_importer.reload()
        cleaned = gc.collect()
        if Lib.config["verbose"]:
            Lib.debug("Objects collected: %d, totally unreachable: %d" % \
                      (cleaned, gc.collect()))
        sys.python_logger.separator()
        return
    
    # Catch exception in func and display traceback dialog
    def debug_catch( func, *args, **kwargs ):
        need_retry = True
        while need_retry:
            try: return func(*args, **kwargs)
            except:
                import Tanita2
                if not Lib.config['editor']: Tanita2.show_cursor(True)
                action = display_traceback()
                if not Lib.config['editor']: Tanita2.show_cursor(False)
                if TracebackDialog.TB_RETRY == action:
                    Lib.engine.on_reload()
                    continue
                need_retry = False
                if TracebackDialog.TB_BREAK == action:
                    if not Lib.config['editor']: Tanita2.show_cursor(True)
                    raise RuntimeError("User break.")
        return
    
    # Display traceback window
    def debug_display_traceback():
        global traceback_dlg
        tb_message = sys.stderr.engine_traceback() + traceback.format_exc()
        sys.stderr.traceback(tb_message)
        return traceback_dlg.ShowModal(tb_message)
    
    # Initialization
    def debug_on_init( parent_hwnd ):
        Lib.parent_hwnd = parent_hwnd
        
        # Initializing wxWidgets application
        global wxapplication
        wxapplication = MyApplication()
        sys.stdout = Tanita2._PythonLogger()

        # Engine window handle wrapper
        global parent_window
        parent_window = wx.Frame(None)
        parent_window.SetHWND(parent_hwnd)
        wxapplication.SetTopWindow(parent_window)
        Lib.parent_window = parent_window
        
        # Loading traceback dialog
        global traceback_dlg
        traceback_dlg = TracebackDialog('Lib/engine.xrc')
        
        if not Lib.config['editor'] and Lib.config['console']:
            from wx.py.crust import Crust
            wxapplication.shell_window = wx.Frame(parent_window,
                style=wx.FRAME_FLOAT_ON_PARENT | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | 
                wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLIP_CHILDREN)
            wxapplication.shell_window.Bind(wx.EVT_CLOSE, lambda e: None)
            wxapplication.shell_window.crust = Crust(wxapplication.shell_window)
            
            wxapplication.shell_window.Iconize()
            wxapplication.shell_window.Layout()
            wxapplication.shell_window.Show()
        return
    
    # Script updating function
    def debug_on_frame( dt, just_redraw, cursor_position, mouse_buttons ):
        if Lib.config['left_handed_mouse']:
            bit1 = (mouse_buttons & 1)
            bit2 = (mouse_buttons & 2) >> 1
            mouse_buttons = mouse_buttons & 0xFC | (bit1 << 1) | bit2
        
        Globals.mouse_buttons = mouse_buttons
        Globals.mouse_position = cursor_position
        Globals.cursor_position = cursor_position / Globals.zoom - Globals.location.position
        
        # Traceback dialog and log file hacks
        try: sys.stderr.flush()
        except: pass
        global traceback_dlg
        if just_redraw: return not traceback_dlg.dlg.IsModal()
        
        # wxWidgets message loop
        global wxapplication
        while wxapplication.Pending(): wxapplication.Dispatch()
        wxapplication.ProcessIdle()
        return True
    
    # Cleanups
    def debug_on_cleanup():
        global parent_window
        parent_window.SetHWND(0)
        return
    
    # Overriding module functions with debug ones
    display_traceback = debug_display_traceback
    reload_modules = debug_reload_modules
    catch = debug_catch
    on_init = debug_on_init
    on_frame = debug_on_frame
    on_cleanup = debug_on_cleanup
