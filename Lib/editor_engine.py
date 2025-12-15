"""
Script engine for editor mode.
"""
import common
from Lib import debug

def on_init( parent_hwnd ):
    """
    Python engine initialization function.
    Called by engine after C++ initializations.
    """
    # Adding verbosity to garbage collector
    import gc
    def collect():
        import gc
        n = gc._old_collect()
        debug("Unreachable objects: %d; Garbage: %s" % (n, str(gc.garbage)))
        return n
    gc._old_collect = gc.collect
    gc.collect = collect
    
    # Initializing editor
    common.on_init(parent_hwnd)
    common.catch(__editor_on_init)
    return

def on_reload():
    """
    Python engine reinitialization function.
    Called by engine when reload is needed.
    """
    common.catch(__editor_on_cleanup)
    common.reload_modules()
    common.catch(__editor_on_init)
    return

def on_frame( dt, just_redraw, cursor_position, mouse_buttons ):
    """
    Function to be called each frame from engine.
    \param  dt  time between frames.
    """
    if not common.on_frame(dt, just_redraw, cursor_position, mouse_buttons):
        return
    common.catch(__editor_on_frame, dt)
    return

def on_move_request( x_direction, y_direction, shift_pressed ):
    """
    Function to be called when user tries to move object by
    arrow keys.
    \param  x_direction    -1 - left, +1 - right, 0 - stay
    \param  y_direction    -1 - up, +1 - down, 0 - stay
    \param  shift_pressed  true if shift key is down
    """
    common.catch(__editor_move, x_direction, y_direction, shift_pressed)
    return

def on_cleanup():
    """
    Python engine cleanup function.
    Called by engine before C++ cleanup.
    """
    common.catch(__editor_on_cleanup)
    common.on_cleanup()
    return

def on_keypress( keycode ):
    """
    Python engine key press handler
    Called by engine when key is pressed.
    """
    common.catch(__editor_on_keypress, keycode)
    return

def __editor_on_init():
    import Editor
    Editor._editor.construct()
    return

def __editor_on_frame(dt):
    import Editor
    Editor._editor.on_frame(dt)
    return

def __editor_move(x_direction, y_direction, shift_pressed):
    import Editor
    Editor._editor.on_move_request(x_direction, y_direction, shift_pressed)
    return

def __editor_on_cleanup():
    import Editor
    Editor._editor.on_cleanup()
    return

def __editor_on_keypress( keycode ):
    import Editor
    Editor._editor.on_keypress(keycode)
    return
