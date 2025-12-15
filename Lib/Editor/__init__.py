"""
Editor module for tanita2 engine
"""
import sys, Lib, Lib.Globals, EditorGlobals

# Editor application class
class Editor:
    def construct(self):
        sys.modules['Core'] = sys.modules['Globals'] = sys.modules['Tanita2']

        # Creating list of base classes
        EditorGlobals.object_bases['None'] = ''
        import CommonClasses
        for c in CommonClasses.__all__:
            name = CommonClasses.__dict__[c].__doc__.strip() or 'Unnamed class'
            EditorGlobals.object_bases[name] = c

        del sys.modules['Core'], sys.modules['Globals']
        
        # Initializations
        Lib.Globals.zoom = 1.0
        
        from PropertyWindow import PropertyWindow
        self.property_window = PropertyWindow(Lib.parent_window)
        
        from BrowserWindow import BrowserWindow
        self.browser_window = BrowserWindow(Lib.parent_window)
    
    def on_frame(self, dt):
        self.browser_window.on_frame(dt)
            
    def on_move_request(self, x_direction, y_direction, shift_pressed):
        self.browser_window.on_move_request(x_direction, y_direction, shift_pressed)
            
    def on_cleanup(self):
        self.browser_window.on_cleanup()
        self.property_window.on_cleanup()
        
    def on_keypress(self, keycode):
        pass
    
# Creating editor instance
_editor = Editor()
