'''
Core definitions and wrappers for engine classes

'''

# Adding Overrides package to path
overrides_path = 'CommonClasses/Overrides'
import sys
sys.path.append(overrides_path)

# Imports
from Tanita2 import *
from States import *
from Cursor import *
from Messages import *
from Timer import *
from Settings import *
from Environment import *
from Unitest import *

from Location import *
from Regions import *
from Point import *
from random import randint, uniform as random

# Removing overrides from path
sys.path.remove(overrides_path)

# Music
music = None

# Cursor object
cursor = None

# Flags object
triggers = None
engine = None

# Message manager
messages = None

# Timer object
timer = None

# Jump to location
jump_to_location = None

# Settings
settings = None

# Tray object
tray = None

# Персонажи.
active_character = None
second_character = None

# Video player
video = None

# Ingame menu
ingame = None

# Environment
environment = None

# Fading
fading = None

RESOURCE_TYPE_WAV = ResourceType.RESOURCE_TYPE_WAV
RESOURCE_TYPE_RGN = ResourceType.RESOURCE_TYPE_RGN
RESOURCE_TYPE_PTH = ResourceType.RESOURCE_TYPE_PTH
RESOURCE_TYPE_PNG = ResourceType.RESOURCE_TYPE_PNG


# All exported definitions
__all__ = ['vec2', 'Location', 'Layer', 'LayerImage', 'AnimatedObject', 'Unitest',
           'State', 'Cursor', 'Timer', 'TimerState', 'Path', 'KeyPoint', 'Point',
        
           'Location', 'Region', 'ZRegion', 'BlockRegion', 'WalkRegion',
        
           'CURSOR_NORMAL', 'CURSOR_ACTIVE',  'CURSOR_TAKE', 'CURSOR_APPLY',
           'CURSOR_GOTO', 'CURSOR_IGNORE', 'CURSOR_TALK',
        
           'randint', 'random',
        
           'cursor', 'timer', 'tray', 'triggers', 'engine', 'settings', 
           'jump_to_location', 'music', 'video', 'messages', 'environment',

           'ResourceId',
           'RESOURCE_TYPE_WAV', 'RESOURCE_TYPE_PNG', 'RESOURCE_TYPE_RGN', 'RESOURCE_TYPE_PTH']
