"""
Python part of Tanita2 game engine.
'Lib' module.

Project-wide declarations:
    config           - dict with configuration options
    engine           - current engine module object
    
    def error(msg)   - print error message
    def debug(msg)   - print debug message
"""
import sys

sys.python_logger = sys.stdout

def error(msg):
    '''
    Print error message to log file
    '''
    sys.python_logger.write_warning(msg)
    return
    
def debug(msg):
    '''
    Print debug message to log file
    '''
    sys.python_logger.write_debug(msg)
    return

# Configuration database
config = None

# Engine module object
engine = None

# Parent window handle and instance
parent_hwnd = None
parent_window = None

# Load configuration file
def configure( conf ):
    """
    Loads configuration file and initializes
    engine configuration database.
    Called from C++ engine in configuration
    system initialization.
    \param  conf  pre-filled options dict from engine
    """
    import warnings
    warnings.filterwarnings('ignore', 'Non-ASCII character .*/peps/pep-0263',
                            DeprecationWarning)
    
    # Class for handling configuration options
    class Config:
        def __init__(self, dictionary, immutables):
            self.__dict = dictionary
            self.__immutables = immutables
            return
        def __getitem__(self, key):
            try: return self.__dict[key]
            except KeyError: raise KeyError('Invalid configuration value: "%s"' % key)
        def __setitem__(self, key, value):
            if key in self.__immutables:
                raise Exception('Configuration parameter "%s" is read-only' % key)
            self.__dict[key] = value
        def has_key(self, key):
            return self.__dict.has_key(key)
        def __str__(self):
            return '\n'.join(['Configuration options:', '@<P'] + \
                             ['    %s: %s' % (k, v) for k, v in self.__dict.iteritems()] + \
                             ['@>P'])
    
    # Setting up default values
    from config import defaults, immutables
    for key, value in defaults.iteritems(): conf[key] = value
    # Applying overrides
    if conf["debug"]:
        from config import defaults_debug_overrides as defaults
        for key, value in defaults.iteritems(): conf[key] = value
    if conf["editor"]:
        from config import defaults_editor_overrides as defaults
        for key, value in defaults.iteritems(): conf[key] = value
    
    # Opening configuration file
    try: f = file(conf['config_filename'], 'rt')
    except IOError: error('Unable to open configuration file "%s"' % \
                          conf['config_filename'])
    else:
        # Reading values from configuration file
        values = {}
        try: exec f in {'true': True, 'false': False, 
                        'editor_mode': conf['editor'], 
                        'debug_mode': conf['debug'],
                        }, values
        except:
            error('Configuration file "%s" contains errors' % \
                  conf['config_filename'])
        for key, value in values.iteritems(): conf[key] = value
    global config
    config = Config(conf, immutables)
    print config

    if config['do_profile']:
        import psyco
        psyco.log('profile.log')
        psyco.profile()
    
    # Loading scripts for current engine mode
    engine_name = (config["editor"] and "editor_engine" or "engine")
    global engine
    engine = __import__("Lib." + engine_name, globals(), {}, ["0"])
    return config
