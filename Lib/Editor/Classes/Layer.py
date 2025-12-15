'''
Layer tree element
'''
import wx, shutil, os, os.path, md5, Tanita2
from Lib.Editor import EditorGlobals
from weakref import proxy
from Misc import ItemBase
from StaticImage import StaticImage
from Region import Region
from Path import Path
from AnimatedObject import AnimatedObject
from Point import Point

class Layer(ItemBase):
    ''' Layer class '''
    
    def __init__(self, name, parent):
        self.volatile_objects = ['layer']
        self.is_visible = True
        self.parallax_x = 0
        self.parallax_y = 0
        self.panel_description = ['LAYER_PROPS', {'hori'  : 'HORIZONTAL',
                                                  'vert'  : 'VERTICAL'}]
        ItemBase.__init__(self, name, parent, wx.ART_LAYER)
        
    def create_volatile_objects(self, parent):
        ItemBase.create_volatile_objects(self, parent, ['eye'])
        self.controls['eye'].Bind(wx.EVT_LEFT_UP, lambda e: self.__toggle_visibility())
        
        self.__set_visibility()
        self.parent.location.objects[self.name] = Tanita2.Layer()
        self.layer = proxy(self.parent.location.objects[self.name])
        
        self.layer.parallax.x = self.parallax_x
        self.layer.parallax.y = self.parallax_y

    def on_menu(self, event):
        ''' Show context menu '''
        if self.is_visible:
            return [('New background image', wx.ART_STATIC, self.__on_new_image),
                    ('New region', wx.ART_REGION, lambda e: self.create_new_region(self)),
                    ('New path',   wx.ART_PATH, lambda e: self.create_new_path(self)),
                    ('New object', wx.ART_OBJECT, lambda e: self.create_new_object(self)),
                    ('New point',  wx.ART_POINT, lambda e: self.create_new_point(self)),
                    (None,),
                    ('Rename'),
                    (None),
                    ('Delete', wx.ART_DELETE, self.__on_delete),]
        else:
            return [('Show', wx.ART_SHOW, lambda e: self.__toggle_visibility()),
                    (None,),
                    ('Delete', wx.ART_DELETE, self.__on_delete),]
    
    def __on_new_image(self, event):
        path = self.fileopen_dialog("PNG files (*.png)|*.png", wx.OPEN | wx.FILE_MUST_EXIST)
        if None == path: return
        
        if not path.startswith(EditorGlobals.art_folder):
            wx.MessageBox('Images should be loaded from "%s" folder' % EditorGlobals.art_folder)
            return

        # Copying file inside local art folder
        target_name = 'art\\%x.png' % self.hash(path[len(EditorGlobals.art_folder):])
        if os.path.isfile(target_name):
            if md5.new(file(path, 'rb').read()).hexdigest() != md5.new(file(target_name, 'rb').read()).hexdigest():
                wx.MessageBox('File with the same hash already exists. Rewritten.',
                              'Warning')
                #### TODO: Show image comparison dialog
                shutil.copy(path, target_name)
        else: shutil.copy(path, target_name)
        
        self.track()
        name = self.guess_name(self.children, os.path.splitext(os.path.split(path)[1])[0])

        img = self.children[name] = StaticImage(name, self, target_name, path)
        center = self.get_screen_center()
        self.children[name].set_position([center[0] - img.image.sequence.bounding_box.x/2,
                                          center[1] - img.image.sequence.bounding_box.y/2])
        
        self.tree.SelectItem(self.children[name].item)
    
    @staticmethod
    def create_new_point(self, position=None):
        self.track()
        name = self.guess_name(self.children, 'Point')

        img = self.children[name] = Point(name, self)
        if not position: position = self.get_screen_center()
        self.children[name].set_position(position)
        
        self.tree.SelectItem(self.children[name].item)
    
    @staticmethod
    def create_new_region(parent):
        parent.track()
        name = parent.guess_name(parent.children, 'region')
        reg = parent.children[name] = Region(name, parent)
        parent.tree.SelectItem(parent.children[name].item)
        
    @staticmethod
    def create_new_path(parent):
        parent.track()
        name = parent.guess_name(parent.children, 'path')
        reg = parent.children[name] = Path(name, parent)
        parent.tree.SelectItem(parent.children[name].item)
    
    @staticmethod
    def create_new_object(parent):
        parent.track()
        name = parent.guess_name(parent.children, 'object')
        parent.children[name] = AnimatedObject(name, parent)
        parent.children[name].set_position(parent.get_screen_center())
        parent.tree.SelectItem(parent.children[name].item)
        parent.children[name].add_sequence()
        parent.tree.SelectItem(parent.children[name].item)
    
    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
        
        self.track()
        
        self.tree.Delete(self.item)
        del self.parent.location.objects[self.name]
        del self.parent.children[self.name]
        del self.children
        del self.layer
    
    def __set_visibility(self):
        if not self.is_visible:
            self.tree.SetItemTextColour(self.item, wx.Color(128, 128, 128))
            self.tree.Collapse(self.item)
            self.controls['eye'].SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_HIDE))
        else:
            self.tree.SetItemTextColour(self.item, wx.Color(0, 0, 0))
            self.controls['eye'].SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_SHOW))
            
    def get_object(self): return self.layer
    
    def __toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.__set_visibility()
        if self.is_visible: self.tree.Expand(self.item)
        
    def on_panel_show(self):
        self.panel.window.Bind(wx.EVT_SCROLL_CHANGED, self.__on_x_para_scroll, self.panel.hori)
        self.panel.window.Bind(wx.EVT_SCROLL_CHANGED, self.__on_y_para_scroll, self.panel.vert)
        
        self.panel.hori.SetValue(self.parallax_x * 1000)
        self.panel.vert.SetValue(self.parallax_y * 1000)
        
    def on_panel_hide(self):
        self.parallax_x = self.panel.hori.GetValue() / 1000.0
        self.parallax_y = self.panel.vert.GetValue() / 1000.0

    def __on_x_para_scroll(self, event):
        self.track()
        self.parallax_x = self.panel.hori.GetValue() / 1000.0
        self.layer.parallax.x = self.parallax_x
        
    def __on_y_para_scroll(self, event):
        self.track()
        self.parallax_y = self.panel.vert.GetValue() / 1000.0
        self.layer.parallax.y = self.parallax_y
        
    def check(self):
        pass
                    
    def export(self, path):
        if not os.path.isdir(path):
            os.mkdir(path) 
        j = file(os.path.join(path, '__init__.py'), 'wt')
        j.write(


"""# This file is generated automatically.
# Please don't edit it by hand because your
# changes will be rewritten by editor.

from Core import *
from %sLayer import %sLayer as User%sLayer

class %sLayer(Layer, User%sLayer):
    def __init__(self):
        Layer.__init__(self)
        User%sLayer.__init__(self)
        
        self.parallax = %s
        
""" % (self.name, self.name, self.name, self.name, self.name, self.name, Tanita2.vec2(self.parallax_x, self.parallax_y)))

        for obj in self.children.itervalues():
            if obj.__class__ is Point:
                j.write(
"""             
        point = self.objects['%s'] = Point()
        point.position = vec2(%f, %f)
        self.point%s = point
""" % (obj.name, int(obj.get_position()[0]), int(obj.get_position()[1]), obj.name))
        j.write("\n")

        for obj in self.children.itervalues():
            if obj.__class__ is Path:
                pth_path = 'art\\%x.pth' % self.hash(os.path.join(path, '%s.pth' % obj.name))
                obj.path.save(pth_path)
                j.write(
"""        path = self.objects['%s'] = Path()
        path.load(%s)
        path.position = vec2(%f, %f)
        path.affect_position = %s
        path.relative_movement = %s
        path.affect_rotation = %s
        path.relative_rotation = %s
        %s
        self.path%s = path

""" % (obj.name, obj.pth_path_ID(pth_path),
       int(obj.get_position()[0]), int(obj.get_position()[1]),
       obj.affect_pos, obj.rel_move, obj.affect_rot, obj.rel_rot,
       '\n        '.join(["path.key_points['%s'] = KeyPoint(%d, %d)" % (n, k.index, k.speed) 
                     for n, k in obj.path.key_points.iteritems()]), obj.name))
        j.write("\n")



        for obj in self.children.itervalues():
            if obj.__class__ is StaticImage:
                j.write(
"""        img = self.objects['%s'] = LayerImage()
        img.load_image(%s, %s)
        img.position = vec2(%f, %f)

""" % (obj.name, obj.image_path_ID(), obj.is_compressed,
       int(obj.get_position()[0]), int(obj.get_position()[1])))

            elif obj.__class__ is Region:
                j.write(obj.dump('        ', path))
            elif obj.__class__ is AnimatedObject:
                # Z regions go before object
                for c in obj.children.itervalues():
                    if c.__class__ is not Region or c.type != 'Z': continue
                    name = self.guess_name(self.children, "%s_%s" % (obj.name, c.name))
                    rgn_path = 'art\\%x.rgn' % self.hash(os.path.join(path, '%s.rgn' % name))
                    c.region.save(rgn_path)
                    j.write(
"""        rgn = self.objects['%s'] = ZRegion()
        rgn.load(%s)
        rgn.position = vec2(%f, %f)

""" % (name, c.rgn_path_ID(rgn_path),
       int(c.get_position()[0] + obj.get_position()[0]),
       int(c.get_position()[1] + obj.get_position()[1])))

                tab = ''
                prefix = ''
                if obj.base_class == 'TrayItem' or obj.base_class == 'BonusItem':
                    obj.conditional_load = True
                if obj.conditional_load:
                    tab = ' ' * 4
                    prefix = "if self.should_load_%s():\n%s        " % (obj.name, tab)
                j.write(
"""        # '%s' child object
        %sfrom %sPackage import %s
        %sobj = self.objects['%s'] = %s()
        %sif not getattr(obj, "affect_position", False):
        %s    obj.position = vec2(%f, %f)
        %sself.obj%s = obj

""" % (obj.name, prefix, obj.name, obj.name, tab, obj.name, obj.name, tab, tab,
       int(obj.get_position()[0]), int(obj.get_position()[1]),
       tab, obj.name))
                obj.export(os.path.join(path, "%sPackage" % obj.name))
        j.close()

        # Template for user script file
        if not os.path.exists(os.path.join(path, '%sLayer.py' % self.name)):
            j = file(os.path.join(path, '%sLayer.py' % self.name), 'wt')
            j.write(
"""# Generated automatically.
# This file can be edited safely.

from Core import *

class %sLayer:
    def __init__(self):
        # Todo: Write class specific initialization,
        # create additional states, redefine handlers and
        # links for states generated by editor.
        pass
""" % (self.name))
            j.close()
