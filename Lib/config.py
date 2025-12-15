"""
Definitions for initial configuration fields and
readonly fields.
"""

# Default configuration values
defaults = \
{
    # Window position (default - CW_USEDEFAULT)
    'x':              -2147483648,
    'y':              -2147483648,
    # Window client area width and height
    'width':          1024,
    'height':         768,
    # Actual window width and height
    'actual_width':   1024,
    'actual_height':  768,
    # Fullscreen vs windowed mode
    'windowed':       False,
    # Refresh rate (fullscreen only)
    'refresh_rate':   75,
    # Vertical syncronization flag
    'vertical_sync':  True,
    # Don't show log file on errors
    'display_log_file': False,

    # Disable file caching
    'disable_file_cache': False,

    # Enable load of cached dds instead of png
    'enable_dds_load': False,

    # Use packed files loader
    'use_pack_loader': True,
    
    # Sound sample rate, Hz
    'sound_sample_rate': 44100,
    # Sound bits per sample
    'sound_bits_per_sample': 16,
    
    # Use wxWindows logging system to log errors
    'use_wx_log': False,

    # Show debug console
    'console': False,
    
    # Verbosity flag
    'verbose': False,
    
    # Percents of video memory to clean when out-of-memory error
    'vmem_hyst': 20,
    # Video memory size to use in Kb
    'video_memory_limit': -1,
    # Threshold of available memory to begin garbage collection, Mb
    'free_sysmem_threshold': -1,
    
    # Left-handed mouse enable flag
    'left_handed_mouse': False,
    
    # Rendering to texture support
    'enable_render_to_texture' : True,

    # Profiling flag
    'do_profile' : False,

    # Music volume
    'music_volume' : 65,
    
    # Use startup location from junctions file instead of interface.
    'use_startup_location' : False,
    
    # Print FPS counter.
    'print_fps' : False,
    
    'use_saves_dir' : False,
}

# Configuration value overrides for debug mode
defaults_debug_overrides = \
{
    # Show log file on errors
    'display_log_file': True,
    
    # Verbosity flag
    'verbose': True,

    # Use packed files loader
    'use_pack_loader': False,
    
    # Use startup location from junctions file instead of interface.
    'use_startup_location' : True,
}

# Configuration value overrides for editor mode
# Applied after debug overrides.
defaults_editor_overrides = \
{
    # Window position with editor windows
    'x':              350,
    'y':              0,
    # Use wxWindows logging system to log errors
    'use_wx_log':     True,
    # Verbosity flag
    'verbose':        False,
    
    # Threshold of available memory to begin garbage collection, Mb
    'free_sysmem_threshold': 200,

    # Use packed files loader
    'use_pack_loader': False,
    
    # Use startup location from junctions file instead of interface.
    'use_startup_location' : True,
}

# List of immutable field names
# Immutable field cannot be changed after configuration
# file parsing.
immutables = \
[
    'debug',
    'editor',
    'width',
    'height',
    'windowed',
    'refresh_rate',
    'vertical_sync',
    'sound_sample_rate',
    'sound_bits_per_sample',
    'display_log_file',
    'use_wx_log',
    'vmem_hyst',
    'video_memory_limit',
    'free_sysmem_threshold',
    'console',
    'enable_dds_load',
    'use_pack_loader',
]
