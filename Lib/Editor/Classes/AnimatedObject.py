'''
AnimatedObject class
'''
from weakref import proxy
import wx, Tanita2, Gizmos, os, os.path, md5, shutil
from Lib.Editor import EditorGlobals
from Misc import ItemBase
from Sequence import AnimatedSequence
from Separator import Separator
from Region import Region
from Sound import Sound
from SequenceSound import SequenceSound

class AnimatedObject(ItemBase):
    ''' AnimatedObject class '''

    def __init__(self, name, parent):
        self.__position = [0, 0]
        self.pivot_position = [0, 0]
        self.initial_animation = None
        self.conditional_load = False
        self.base_class = ''
        self.comment = ''
        ItemBase.__init__(self, name, parent, wx.ART_OBJECT)

    def is_inside(self, pos):
        if self.is_selected and self.affect_pivot:
            return self.animation.objects['_gizmo_'].objects['_gizmo_hotspot_'].is_inside(pos)

        if self.animation.state != '?__special_state__?':
            return self.animation.sequences[self.animation.state].is_inside(pos)
        return False

    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        old_pos = self.__position[:]
        self.__position = list(new_pos)
        self.animation.position = Tanita2.vec2(new_pos[0], new_pos[1])
        if self.affect_pivot:
            self.pivot_position[0] += new_pos[0] - old_pos[0]
            self.pivot_position[1] += new_pos[1] - old_pos[1]
            for c in self.children.itervalues():
                if not hasattr(c, 'get_position'): continue
                p = c.get_position()
                p[0] -= new_pos[0] - old_pos[0]
                p[1] -= new_pos[1] - old_pos[1]
                c.set_position(p)

    def get_screen_center(self):
        return [-self.pivot_position[0], -self.pivot_position[1]]

    def animation_path_ID(self):
        name = self.animation_path.split('\\')[1]
        return "ResourceId(0x%s, RESOURCE_TYPE_PNG)" % (name.lower())

    def __new_object(self, what):
        p = self.parent
        while None != p:
            if hasattr(p.__class__, what):
                return getattr(p.__class__, what)(self)
            p = p.parent

    def __new_object_2(self, what, *arg):
        p = self.parent
        while None != p:
            if hasattr(p.__class__, what):
                return getattr(p.__class__, what)(p, *arg)
            p = p.parent

    def on_menu(self, event):
        ''' Show context menu '''
        return [('New region', wx.ART_REGION, lambda e: self.__new_object('create_new_region')),
                ('New object', wx.ART_OBJECT, lambda e: self.__new_object('create_new_object')),
                (None),
                ('Add sequence', wx.ART_ANIMATION, lambda e: self.add_sequence()),
                ('Add sound', wx.ART_SOUND, lambda e: self.add_sound()),
                (None),
                ('Rename'),
                (None),
                ('Delete', wx.ART_DELETE, self.__on_delete),]

    def __topower2(self, n):
        x = 2
        while n > x: x <<= 1
        return x

    def add_sequence(self):
        path = self.fileopen_dialog("PNG files (*.png)|*.png", wx.OPEN | wx.FILE_MUST_EXIST)
        if None == path: return

        if not path.startswith(EditorGlobals.art_folder):
            wx.MessageBox('Images should be loaded from "%s" folder' % EditorGlobals.art_folder)
            return

        directory, fname = os.path.split(path)
        i = os.path.splitext(fname)[0]
        try: i = int(i)
        except ValueError:
            wx.MessageBox('Sequence images should be named (number).png', 'Error')
            return
        # Searching for min and max image index
        minindex = maxindex = i
        j = k = i
        while True:
            j -= 1
            if j < 0 or not os.path.exists(os.path.join(directory, 
                                           '%d.png' % j)): minindex = j+1; break
        while True:
            k += 1
            if k < 0 or not os.path.exists(os.path.join(directory, 
                                           '%d.png' % k)): maxindex = k-1; break
        
        indices = xrange(minindex, maxindex+1)
        if len(indices) > 1 and wx.ID_YES != self.yesno_dialog(
            'Do you want to import whole sequence? (%d frames)' % len(indices)):
            indices = [i]

        # Copying sequence to engine
        target_name = 'art\\%x' % self.hash(directory)
        if not os.path.isdir(target_name):
            os.mkdir(target_name)

        size = 0
        rewritten_count = 0
        import PIL.Image as Image
        for i in indices:
            old_path = os.path.join(directory, '%d.png' % i)

            im = Image.open(old_path)
            w, h = im.size
            w = self.__topower2(w)
            h = self.__topower2(h)
            size += long(w) * h * 4
            del im

            path = os.path.join(target_name, '%d.png' % i)
            if os.path.exists(path):
                if md5.new(file(old_path, 'rb').read()).hexdigest() != md5.new(file(path, 'rb').read()).hexdigest():
                    rewritten_count += 1
                #### TODO: Show image comparison dialog
                    shutil.copy(old_path, path)
            else: shutil.copy(old_path, path)
        if rewritten_count:
            wx.MessageBox('Some files were updated with new version from art folder.\n' +
                          'Number of updated files: %d' % rewritten_count, 'Warning')
        self.track()
        seq_name = os.path.split(directory)[1]
        if not seq_name: seq_name = 'sequence'
        name = self.guess_name(self.children, seq_name)

        if len(self.animation.sequences) == 0:
            self.initial_animation = name
        index = 0
        for c in self.children.itervalues():
            if c.__class__ is Separator and c.id == self.id_children: break
            index += 1
        print 'Sequence size: %d Mb' % (size / 1048576)
        self.children.insert(index, name, AnimatedSequence(name, self, target_name, 
                                                           indices, size / 1048576 > 15,
                                                           original_path=directory))
        self.children[name].set_position([-self.pivot_position[0], -self.pivot_position[1]])
        self._update_item_order()
        self.tree.SelectItem(self.children[name].item)
    
    def add_sound(self):
        path = self.fileopen_dialog("WAV files (*.wav)|*.wav", wx.OPEN | wx.FILE_MUST_EXIST)
        if None == path: return

        if not path.startswith(EditorGlobals.art_folder):
            wx.MessageBox('Sounds should be loaded from "%s" folder' % EditorGlobals.art_folder)
            return

        # Copying sound to engine
        target_name = 'art\\%x.wav' % self.hash(path[len(EditorGlobals.art_folder):])
        if os.path.isfile(target_name):
            if md5.new(file(path, 'rb').read()).hexdigest() != md5.new(file(target_name, 'rb').read()).hexdigest():
                wx.MessageBox('File with the same hash already exists. Rewritten.',
                              'Warning')
                shutil.copy(path, target_name)
        else: shutil.copy(path, target_name)
        
        self.track()
        name = self.guess_name(self.children, os.path.splitext(os.path.split(path)[1])[0])

        index = 0
        for c in self.children.itervalues():
            if c.__class__ is Separator and c.id == self.id_sequences: break
            index += 1
        self.children.insert(index, name, Sound(name, self, target_name, path))
        snd = self.children[name]
        center = self.get_screen_center()
        self.children[name].set_position([center[0] - snd.gizmo.width/2,
                                          center[1] - snd.gizmo.height/2])
        self._update_item_order()
        self.tree.SelectItem(self.children[name].item)

    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return

        self.track()
        self.tree.Delete(self.item)
        del self.parent.get_object().objects[self.name]
        del self.parent.children[self.name]

    def get_object(self): return self.animation

    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''

        self.item_is_selected = False
        self.bases = EditorGlobals.object_bases

        self.panel_description = ['OBJECT_PROPS', {'seqs' : 'SEQUENCES',
                                                   'pivot': 'PIVOT_BTN',
                                                   'newp':  'DROP_POINT',
                                                   'bases': 'BASES',
                                                   'load':  'CONDITIONAL',
                                                   'comment' : 'COMMENT'}]
        # Compatibility layer
        if not hasattr(self, 'pivot_position'):
            self.pivot_position = [0, 0]
        if not hasattr(self, 'base_class'):
            self.base_class = ''
        else:
            if self.base_class == 'TrayItem' or self.base_class == 'BonusItem':
                self.conditional_load = True
        if not hasattr(self, 'is_visible'):
            self.is_visible = True
        if not hasattr(self, 'conditional_load'):
            self.panel.conditional_load = False
        if not hasattr(self, 'comment'): self.comment = ''
        
        self.id_sequences = "sequences"
        self.id_sounds = "sounds"
        self.id_children = "children"

        self.volatile_objects = ['animation', 'gizmo', 'affect_pivot']
        ItemBase.create_volatile_objects(self, parent, ['lock', 'eye'])
        
        if self.children.has_key('__separator__'):
            del self.children['__separator__']
        if not self.children.has_key('__sndseparator__'):
            self.children.insert(0, '__sndseparator__', Separator(self, self.id_sounds))
        if not self.children.has_key('__seqseparator__'):
            index = 0
            for i in self.children.itervalues():
                if i.__class__ not in (Sound, Separator): break
                index += 1
            self.children.insert(index, '__seqseparator__', Separator(self, self.id_sequences))
        if not self.children.has_key('__cldseparator__'):
            index = 0
            for i in self.children.itervalues():
                if i.__class__ not in (AnimatedSequence, Separator, Sound): break
                index += 1
            self.children.insert(index, '__cldseparator__', Separator(self, self.id_children))
            
        index1, index2, index3 = 0, 0, 0
        ii = 0
        for i in self.children.itervalues():
            if i.__class__ is Separator:
                if i.id == self.id_sounds: index1 = ii
                if i.id == self.id_sequences: index2 = ii
                if i.id == self.id_children: index3 = ii
            ii += 1
        if index1 > index2:
            assert index2 == 0, 'Bad index, all gone wrong'
            
            self.children.dictionary = self.children.dictionary[index1:index3] + \
                self.children.dictionary[0:index1] + self.children.dictionary[index3:]
        
        self.controls['eye'].Bind(wx.EVT_LEFT_UP, lambda e: self.__toggle_visibility())
        self.__set_visibility()

        self.affect_pivot = False

        class AnimatedObject(Tanita2.AnimatedObject):
            def update(self, dt):
                if not self._parent.is_visible: return
                Tanita2.AnimatedObject.update(self, dt)

        self.parent.get_object().objects[self.name] = AnimatedObject()
        self.animation = proxy(self.parent.get_object().objects[self.name])
        self.animation.position = Tanita2.vec2(self.__position[0], self.__position[1])
        self.animation.states['?__special_state__?'] = Tanita2.State(None, link=self.link_function)
        self.animation.state = '?__special_state__?'
        self.animation._parent = proxy(self)

        self.animation.objects['_gizmo_'] = Gizmos.AnimationGizmo(self, 2, 2, 0xffff0000)
        self.animation.objects['_gizmo_'].objects['_gizmo!'] = \
            Gizmos.Gizmo(16, 16, 0xaaff7f00)
        self.animation.objects['_gizmo_'].objects['_gizmo!'].position = Tanita2.vec2(-7, -7)
        class HotSpotGizmo(Gizmos.SelectionGizmo):
            def update(self, dt):
                if self.parent_object.is_selected and self.parent_object.affect_pivot:
                    Gizmos.SelectionGizmo.update(self, dt)

        self.animation.objects['_gizmo_'].objects['_gizmo_hotspot_'] = \
            HotSpotGizmo(self, 50, 50, 0x55ff0000)
        self.animation.objects['_gizmo_'].objects['_gizmo_hotspot_'].position = Tanita2.vec2(-25, -25)

    def __set_visibility(self):
        if not self.is_visible:
            self.tree.SetItemTextColour(self.item, wx.Color(128, 128, 128))
            self.tree.Collapse(self.item)
            self.controls['eye'].SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_HIDE))
        else:
            self.tree.SetItemTextColour(self.item, wx.Color(0, 0, 0))
            self.controls['eye'].SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_SHOW))

    def __toggle_visibility(self):
        self.is_visible = not self.is_visible
        self.__set_visibility()

    def link_function(self):
        # No animations except empty one
        if 0 == len(self.animation.sequences): return '?__special_state__?'
        if self.animation.state == '?__special_state__?':
            return self.animation.sequences.get_key_by_index(0)

        for c in self.children.itervalues():
            if c.__class__ is not AnimatedSequence: continue
            if self.tree.IsSelected(c.item): return None

        # No sequences selected - showing next by order if needed
        if self.animation.sequences[self.animation.state].is_over:
            i = self.animation.sequences.get_index(self.animation.state)
            i = (i + 1) % len(self.animation.sequences)
            self.animation.sequences.get_by_index(i).frame = 0
            return self.animation.sequences.get_key_by_index(i)
        return None

    def _get_pos_object(self): return self.__position[:]

    def on_end_drag(self, over_object):
        from Region import Region
        return ItemBase.on_end_drag(self, over_object, [Region], extended=True)

    def __on_pivot_btn(self, event):
        self.affect_pivot = self.panel.pivot.GetValue()
        if self.affect_pivot: self.lock(False)

    def __on_droppoint_btn(self, event):
        ap = self.animation.absolute_position
        lp = EditorGlobals.browser_window.loaded_location.location.position
        pos = [ap.x - lp.x, ap.y - lp.y]
        self.__new_object_2('create_new_point', pos)

    def __on_cond_check(self, e):
        self.conditional_load = self.panel.load.GetValue()

    def on_panel_show(self):
        try: self.animation.sequences
        except: return

        self.panel.pivot.SetValue(self.affect_pivot)
        self.panel.window.Bind(wx.EVT_COMBOBOX, lambda e: self.on_panel_hide())
        self.panel.window.Bind(wx.EVT_TOGGLEBUTTON, self.__on_pivot_btn, self.panel.pivot)
        self.panel.window.Bind(wx.EVT_BUTTON, self.__on_droppoint_btn, self.panel.newp)
        self.panel.window.Bind(wx.EVT_CHECKBOX, self.__on_cond_check, self.panel.load)
        self.panel.load.SetValue(self.conditional_load)
        self.panel.comment.SetValue(self.comment)
        self.panel.seqs.Enable()
        self.panel.seqs.Clear()

        sel_i = -1
        index = 0
        for i in self.animation.sequences.iterkeys():
            if i == self.initial_animation:
                sel_i = index
            self.panel.seqs.Append(i)
            index += 1

        if -1 != sel_i: self.panel.seqs.Select(sel_i)
        else:
            if 0 == len(self.animation.sequences):
                self.panel.seqs.Disable()
                self.initial_animation = None
            else:
                self.panel.seqs.Enable()
                self.initial_animation = self.animation.sequences.get_key_by_index(0)
                self.panel.seqs.Select(0)

        self.panel.bases.Clear()

        sel_i = -1
        i = 0
        for k, v in self.bases.iteritems():
            if v == self.base_class: sel_i = i
            self.panel.bases.Append(k)
            i += 1
        if -1 != sel_i: self.panel.bases.Select(sel_i)

        if self.base_class == 'TrayItem' or self.base_class == 'BonusItem':
            self.panel.load.Disable()
        else:
            self.panel.load.Enable()


    def on_panel_hide(self):
        self.base_class = self.bases[self.panel.bases.GetValue()]

        try:
            if 0 == len(self.animation.sequences): raise
        except: return
        sel = self.panel.seqs.GetSelection()
        if wx.NOT_FOUND == sel: return

        self.initial_animation = self.panel.seqs.GetString(sel)
        self.affect_pivot = False
        self.conditional_load = self.panel.load.GetValue()
        self.comment = self.panel.comment.GetValue()

        if self.base_class == 'TrayItem' or self.base_class == 'BonusItem':
            self.panel.load.Disable()
        else:
            self.panel.load.Enable()


    def check(self):
        if len(self.animation.states) <= 1 and self.initial_animation:
            self.initial_animation = None
        if len(self.animation.states) > 1 and \
           self.initial_animation not in self.animation.states.iterkeys():
            return 'Object %s: invalid initial animation' % self.name
        if self.base_class == 'TrayItem':
            if not self.children.has_key('Take') or self.children['Take'].__class__ is not Region:
                return 'Object %s: Takeables item should have \'Take\' region' % self.name
            for obj in self.children.itervalues():
                if obj.__class__ is Sound and obj.name == self.name[len('Item_'):].capitalize():
                    if obj.looped:
                        return 'Object %s: Sound %s should not looped' % (self.name, obj.name)
                    if not obj.prolonged:
                        return 'Object %s: Sound %s must be prolonged' %  (self.name, obj.name)
        if self.base_class == 'TrayItem' and not self.name.startswith('Item_'):
            return 'Object %s: Takeables item should have name \'Item_name\'' % self.name
        if self.base_class == 'BonusItem' and (not self.children.has_key('Click') \
           or self.children['Click'].__class__ is not Region):
            return 'Object %s: Bonus item should have \'Click\' region' % self.name
        if self.base_class == 'CommentRegion' and (not self.children.has_key('Click') \
           or self.children['Click'].__class__ is not Region):
            return 'Object %s: comment region should have \'Click\' region' % self.name
        if self.base_class == 'Teleport':
            if not self.name.startswith('Pass_'):
                return 'Object %s: name of Teleport link must be starts with \'Pass_\'' % self.name
            if not self.children.has_key('Click') or self.children['Click'].__class__ is not Region \
                or self.children['Click'].type != 'Junction':
                return 'Object %s: Teleport item should have \'Click\' junction region' % self.name

    def export(self, path):
        if not os.path.isdir(path): 
            os.mkdir(path)

        # Creating wrapped class
        j = file(os.path.join(path, '__init__.py'), 'wt')
        j.write(
"""# This file is generated automatically.
# Please don't edit it by hand because your
# changes will be rewritten by editor.

from Core import *%s
from %s import %s as User%s

class %s(%s%sUser%s):
    def __init__(self):
        # Skipping user class initialization - we'll
        # do it at the end of 'construct' call
        %s

    def construct(self):
""" % (((self.base_class and ['\nfrom CommonClasses import %s as BaseClass' % self.base_class] or [''])[0],) +
       (self.name, ) * 4 + (((self.base_class and self.base_class == 'Fonts') and ('',) or ("AnimatedObject, ",))[0],) +
       ((self.base_class and ['BaseClass, '] or [''])[0],
        self.name, ((self.base_class and self.base_class == 'Fonts') and 'BaseClass.__init__(self)' \
                                                                      or 'AnimatedObject.__init__(self)'))))

        # Adding invisible state
        j.write(
"""        # Empty state
        self.stateEmpty = self.states['__empty__'] = State(None)

""")
        for obj in self.children.itervalues():
            if obj.__class__ is Sound:
                j.write(
"""        # '%s' sound
        self.add_sound('%s', %s)
        snd = self.snd%s = self.sounds['%s']
        snd.position = vec2(%f, %f)
        snd.looped = %s
        snd.prolonged = %s
        snd.volume = %d
        snd.pan = %d
        %s
""" % (obj.name, obj.name, obj.sound_path_ID(), obj.name, obj.name, obj.gizmo.position.x, obj.gizmo.position.y, obj.looped, 
      (self.name[len('Item_'):] == obj.name or self.base_class in ['TrayItem', 'BonusItem']) and obj.prolonged or False, 
      obj.volume, obj.pan, obj.play_when_load and 'snd.play()\n' or ''))

        for obj in self.children.itervalues():
            if obj.__class__ is AnimatedSequence:
                sound_infix = ''
                sound_list = []
                for zz in obj.children.itervalues():
                    if zz.__class__ is SequenceSound:
                        sound_infix = 'sound_'
                        sound_list.append((zz.frame_index, zz.sound_name))
                if sound_list:
                    sound_list = '\n            ('+ ', '.join(['(%d, "%s")' % A for A in sound_list]) + ', ), '
                else:
                    sound_list = ''
                j.write(
"""        # '%s' sequence
        self.add_%ssequence('%s', %s, (%s, ), %s)
        self.state%s = self.states['%s'] = %sState('%s'%s)
        seq = self.sequences['%s']
        seq.position = vec2(%f, %f)
        seq.fps = %d
        seq.looped = %s
        seq.reversed = %s
        seq.horizontal_flip = %s
        seq.vertical_flip = %s
        self.seq%s = seq

""" % ((obj.name, (obj.is_large_sequence and 'large_' or '') + sound_infix,
       obj.name, obj.animation_path_ID(),
       ', '.join([str(i) for i in obj.frame_indices]),
       sound_list + str(obj.is_compressed), obj.name, obj.name,
       obj.ontimer and 'Timer' or '', obj.name, 
       obj.ontimer and (', %s' % str(obj.period)) or '', obj.name,
       int(obj.get_position()[0]), int(obj.get_position()[1]), obj.fps, 
       obj.looped, obj.reversed, obj.horizontal_flip, obj.vertical_flip, obj.name)))


            elif obj.__class__ is Region:
                if obj.type != 'Z':
                    j.write(obj.dump('        ', path))
            elif obj.__class__ is AnimatedObject:
                # Z regions go before object
                for c in obj.children.itervalues():
                    if c.__class__ is not Region or c.type != 'Z': continue
                    name = self.guess_name(self.children, "%s_%s" % (obj.name, c.name))
                    rgn_path = 'art\\%x.rgn' % self.hash(os.path.join(path, '%s.rgn' % name))
                    c.region.save()
                    j.write(
"""        # '%s' z region
        rgn = self.objects['%s'] = ZRegion()
        rgn.load(%s)
        rgn.position = vec2(%f, %f)

""" % (name, name, c.rgn_path_ID(rgn_path),
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
        %sobj = %s()
        %sif not getattr(obj, "affect_position", False):
        %s    obj.position = vec2(%f, %f)
        %sself.obj%s = self.objects['%s'] = obj

""" % (obj.name, prefix, obj.name, obj.name, tab, obj.name, tab, tab,
       int(obj.get_position()[0]), int(obj.get_position()[1]),
       tab, obj.name, obj.name))
                obj.export(os.path.join(path, "%sPackage" % obj.name))

        j.write(
'''        # Setting initial state and saving it
        state = self.state = '%s'

        # Initializing base classes
''' % (self.initial_animation or '__empty__'))

        if self.base_class and self.base_class != 'Fonts':
            j.write('        BaseClass.__init__(self)\n')
        j.write('        User%s.__init__(self)\n' % self.name)

        j.write(
'''
        # Comparing current state with saved one and 
        # calling on_enter if applicable
        if state == self.state and self.states[state].on_enter:
            self.states[state].on_enter()
''')
        j.close()

        # Template for user script file
        if not os.path.exists(os.path.join(path, '%s.py' % self.name)):
            j = file(os.path.join(path, '%s.py' % self.name), 'wt')
            j.write(
"""# Generated automatically.
# This file can be edited safely.

from Core import *

class %s:
    def __init__(self):
        # Todo: Write class specific initialization,
        # create additional states, redefine handlers and
        # links for states generated by editor.
        pass
""" % (self.name))
            j.close()
