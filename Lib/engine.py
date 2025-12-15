"""
Script engine.
"""
import common, sys, Tanita2, Lib
sys.path.extend(['World', 'CommonClasses'])

def on_init( parent_hwnd ):
    """
    Python engine initialization function.
    Called by engine after C++ initializations.
    """
    common.on_init(parent_hwnd)
    common.catch(__engine_on_init)
    if not Lib.config['windowed']:
        Tanita2.setCursorAcceleration(Tanita2.vec2(2, 2))

    return

def on_reload():
    """
    Python engine reinitialization function.
    Called by engine when reload is needed.
    """
    common.catch(__engine_on_cleanup)
    common.reload_modules()
    common.catch(__engine_on_init)
    return

def on_frame( dt, just_redraw, cursor_position, mouse_buttons ):
    """
    Function to be called each frame from engine.
    \param  dt  time between frames.
    """
    if not common.on_frame(dt, just_redraw, cursor_position, mouse_buttons):
        return
    common.catch(__engine_on_frame, dt)
    return

def on_cleanup():
    """
    Python engine cleanup function.
    Called by engine before C++ cleanup.
    """
    common.catch(__engine_on_cleanup)
    common.on_cleanup()
    return

def on_keypress( keycode ):
    """
    Python engine key press handler
    Called by engine when key is pressed.
    """
    common.catch(__engine_on_keypress, keycode)
    return

def __engine_on_init():
    import World
    World._engine.construct()
    return

def __engine_on_frame(dt):
    import World
    World._engine.on_frame(dt)
    return

def __engine_on_cleanup():
    import World
    World._engine.on_cleanup()
    return

def __engine_on_keypress( keycode ):
    import World
    World._engine.on_keypress(keycode)
    return
