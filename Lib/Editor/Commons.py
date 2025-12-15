"""
Helper definitions and common code.
"""
import wx, wx.xrc as xrc, os, EditorGlobals, Tanita2
from Lib import debug, config

class SingletonBase(object):
    '''
    Singleton class
    '''
    def __new__(cls, *args, **kwargs):
        # MyClassName -> my_class_name
        var_name = [cls.__name__[0].lower()]
        for i in xrange(0, len(cls.__name__)-1):
            if cls.__name__[i].islower() and not cls.__name__[i+1].islower():
                var_name.append('_')
            var_name.append(cls.__name__[i+1].lower())
        var_name = ''.join(var_name)
        
        # Creating instance for the first time or returning existing one
        instance = getattr(EditorGlobals, var_name)
        if not instance:
            instance = super(SingletonBase, cls).__new__(cls, *args, **kwargs)
            setattr(EditorGlobals, var_name, instance)
            debug("%s instance created" % cls.__name__)
            return instance
        return

class EditorWindowBase(SingletonBase, wx.MiniFrame):
    '''
    Base class for editor windows
    '''
    def __init__(self, *args, **kwargs):
        wx.MiniFrame.__init__(self, *args, **kwargs)
        
        # Loading resource
        self.resource = xrc.XmlResource('Lib/Editor/icons/resource.xrc')
        if not self.resource: raise IOError("Missing or invalid resource file '%s'" % filename)
        
        # Guessing 'art' folder location
        if config.has_key('art_folder'):
            EditorGlobals.art_folder = config['art_folder']
            return ## PLEASE NOTE THIS!
        cwd = os.getcwd()        
        maxiter = 10
        while 0 < maxiter:
            maxiter -= 1
            cwd = os.path.normpath(os.path.join(cwd, '..'))
            if os.path.splitdrive(cwd)[0]+'\\' == cwd: maxiter = 0; break
            if os.path.isdir(os.path.join(cwd, 'art')): break
            #cwd = os.path.normpath(os.path.join(cwd, '..'))
        if 0 == maxiter:            
            raise RuntimeError, 'There is no \'art\' folder inside project tree'
        config['art_folder'] = os.path.normpath(os.path.join(cwd, 'art')).lower()
        EditorGlobals.art_folder = config['art_folder']
        debug('Art folder location: "%s"' % config['art_folder'])
    
    def yesno_dialog(self, text):
        ''' Display yes-no dialog '''
        dlg = wx.MessageDialog(None, text, "Tanita2 Editor",
                               style=wx.YES | wx.NO | wx.CENTER | 
                               wx.ICON_QUESTION)
        Tanita2.disable_autoactivation(True)
        result = dlg.ShowModal()
        Tanita2.disable_autoactivation(False)
        dlg.Destroy()
        return result
    
    def fileopen_dialog(self, wildcard, style, working_dir=os.getcwd()):
        '''
        Display file open/save dialog.
        Returns relative path on success, None on abort/failure.
        '''
        if os.getcwd() == working_dir:
            if config.has_key('last_working_dir'):
                working_dir = config['last_working_dir']
            else:
                working_dir = EditorGlobals.art_folder
        dlg = wx.FileDialog(None, defaultDir=working_dir,
                            wildcard=wildcard, style=style)
        Tanita2.disable_autoactivation(True)
        retcode = dlg.ShowModal()
        Tanita2.disable_autoactivation(False)
        if retcode != wx.ID_OK: dlg.Destroy(); return None
        orig_path = path = os.path.normpath(dlg.GetPath())
        path = path.lower()
        dlg.Destroy()
        config['last_working_dir'] = os.path.split(path)[0]
        return path
    
    def to_relative_path(self, path):
        '''
        Convert path to relative path (starting from .exe file directory)
        Returns None if path is outside editor directory.
        '''
        lower_path = path.lower()
        base_path = os.path.normpath(os.getcwd()).lower()
        if not lower_path.startswith(base_path): return None
        return path[len(base_path)+1:]
    
    def load_dialog(self, parent, dlg_id):
        '''
        Loading dialog from resource.
        '''
        dlg = self.resource.LoadDialog(parent, dlg_id)
        if not dlg: raise IOError("'%s' resource not found" % dlg_id)
        return dlg

class ToolBar(wx.ToolBar):
    ''' Custom toolbar '''
    
    def __init__(self, parent):
        super(ToolBar, self).__init__(parent, style=wx.TB_FLAT)
        self.SetToolBitmapSize((16, 16))
    
    def AddTool(self, art):
        ''' Add new tool '''
        
        bitmap = wx.ArtProvider.GetBitmap(art, wx.ART_TOOLBAR, (16, 16))
        id = wx.NewId()
        self.AddSimpleTool(id, bitmap)
        self.Realize()
        return id

class ArtProvider(wx.ArtProvider):
    ''' Custom art provider '''
    
    # List of custom bitmaps (name: filename)
    bitmaps = {'ART_UNKNOWN':    'unknown',
               'ART_PROJECT':    'unknown',
               'ART_DELETE':     'delete',
               'ART_RELOAD':     'reload',
               'ART_LOCATION':   'location',
               'ART_LAYER':      'layer',
               'ART_STATIC':     'static',
               'ART_ANIMATION':  'sequence',
               'ART_OBJECT':     'ani',
               'ART_APPLY':      'apply',
               'ART_ZOOM_IN':    'zoomin',
               'ART_ZOOM_RESET': 'zoomr',
               'ART_ZOOM_OUT':   'zoomout',
               'ART_REGION':     'region',
               'ART_SHOW':       'show',
               'ART_HIDE':       'hide',
               'ART_RENAME':     'unknown',
               'ART_LOCK':       'unlock',
               'ART_UNLOCK':     'lock',
               'ART_LOCK_ALL':   'lockall',
               'ART_PLAY':       'play',
               'ART_STOP':       'stop',
               'ART_PAUSE':      'pause',
               'ART_CHECK':      'check',
               'ART_EXPORT':     'export',
               'ART_POINT':      'point',
               'ART_PATH':       'path',
               'ART_SOUND':      'sound',
               'ART_SOUND_SEQ':  'seqsound',
            
               'ART_LOCATION_LOAD' : 'splash',
               'ART_EMPTY':          'empty',
            }
    # Toolbar image list
    image_list = wx.ImageList(16, 16)
    
    def __init__(self, *args, **kwargs):
        wx.ArtProvider.__init__(self, *args, **kwargs)
        
        for art_name, filename in ArtProvider.bitmaps.iteritems():
            setattr(wx, art_name, art_name)
            bmp = wx.Bitmap('Lib/Editor/icons/%s.png' % filename)
            id = ArtProvider.image_list.Add(bmp)
            ArtProvider.bitmaps[art_name] = (bmp, id)
        self.null = wx.NullBitmap
        return
    
    def CreateBitmap(self, artid, client, size):
        ''' Get gitmap from stock '''
        try:
            if ArtProvider.bitmaps.has_key(artid):
                return ArtProvider.bitmaps[artid][0]
        except: pass
        return self.null
    
    @staticmethod
    def GetBitmapId(artid):
        ''' Get bitmap id for image list. '''
        if ArtProvider.bitmaps.has_key(artid):
            return ArtProvider.bitmaps[artid][1]
        raise KeyError('Bitmap "%s" was not registered in ArtProvider' % artid)

# Adding art provider to provider list
wx.ArtProvider.PushProvider(ArtProvider())
