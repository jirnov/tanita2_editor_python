'''
AnimatedObject class
'''
from weakref import proxy
import wx, Tanita2, Gizmos, Lib, os.path, shutil, md5
from Lib.Editor import EditorGlobals
from Misc import ItemBase
from SequenceSound import SequenceSound

class AnimatedSequence(ItemBase):
    ''' AnimatedSequence class '''
    
    def __init__(self, name, parent, animation_path, frame_indices, is_large=False, original_path=''):
        self.animation_path = animation_path
        self.frame_indices = tuple(frame_indices)
        self.original_path = original_path
        
        self.__position = [0, 0]
        self.fps = 15
        self.vertical_flip = False
        self.horizontal_flip = False
        self.looped = False
        self.reversed = False
        self.is_large_sequence = is_large
        self.is_compressed = True
        if is_large: Lib.debug('Large sequence created')
        ItemBase.__init__(self, name, parent, wx.ART_ANIMATION)
    
    def is_inside(self, pos):
        if not self.tree.IsSelected(self.item): return False
        return self.parent.animation.sequences[self.name].is_inside(pos)

    def get_position(self): return self.__position[:]
    def set_position(self, new_pos):
        self.__position = list(new_pos)
        self.parent.animation.sequences[self.name].position = \
            Tanita2.vec2(new_pos[0], new_pos[1])
        self.gizmo.position = Tanita2.vec2(new_pos[0], new_pos[1])
    
    def animation_path_ID(self):
        name = self.animation_path.split('\\')[1]
        return "ResourceId(0x%s, RESOURCE_TYPE_PNG)" % (name.lower())

    def on_menu(self, event):
        ''' Show context menu '''
        return [('Attach sound', wx.ART_SOUND_SEQ, self.__on_sound_attach),
                (None),
                ('Rename', wx.ART_RENAME, self.__on_rename),
                ('Replace', wx.ART_RELOAD, self.__on_replace),
                (None),
                ('Delete', wx.ART_DELETE, self.__on_delete),]
                
    def __on_sound_attach(self, event):
        self.track()
        name = self.guess_name(self.children, 'Sound')
        self.children[name] = SequenceSound(name, self)
        self.tree.SelectItem(self.children[name].item)

    def __on_replace(self, event):
        if len(self.children.itervalues()) > 0 and wx.ID_NO == self.yesno_dialog('All attached sounds will be removed. Continue?'):
            return

        path = self.fileopen_dialog("PNG files (*.png)|*.png", wx.OPEN | wx.FILE_MUST_EXIST)
        if path is None: 
            return

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
            if j < 0 or not os.path.exists(os.path.join(directory, '%d.png' % j)): 
                minindex = j+1
                break
        while True:
            k += 1
            if k < 0 or not os.path.exists(os.path.join(directory, '%d.png' % k)): 
                maxindex = k-1
                break
        
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
        seq_name = os.path.split(directory)[1]
        if not seq_name: seq_name = 'sequence'
        self.track()

        for snd in list(self.children.itervalues()):
            snd.tree.Delete(snd.item)
            if snd.sound_name:
                self._get_seq().del_sound(snd.frame_index, snd.sound_ref)
            del self.children[snd.name]

        self.frame_indices = tuple(indices)
        self.animation_path = target_name
        self.is_large_sequence = size / 1048576 > 15
        self.original_path = directory
        self._update_item_order()

    def __on_rename(self, event):
        ''' Rename relf '''
        new_name = EditorGlobals.browser_window.rename_dialog(self.name, self._check_correct_name)
        if not new_name: return
        self.track()
        
        old_name = self.name
        self.parent.animation.states.change_key(self.name, new_name)
        self.parent.animation.states[new_name].sequence = new_name
        self.parent.animation.sequences.change_key(self.name, new_name)
        self.parent.animation.objects['_gizmo_'].objects.change_key(self.name, new_name)
        
        self.parent.children.change_key(self.name, new_name)
        if self.name == self.parent.animation.state:
            self.parent.animation.states[old_name] = Tanita2.State(None)
            self.parent.animation.state = new_name
            del self.parent.animation.states[old_name]
        if self.name == self.parent.initial_animation:
            self.parent.initial_animation = new_name
        self.name = new_name
        self.tree.SetItemText(self.item, self.name)

    def __on_delete(self, event):
        if wx.ID_YES != self.yesno_dialog('Are you sure?'): return
       
        self.track()
        self.tree.Delete(self.item)
        if self.parent.animation.state == self.name:
            self.parent.animation.state = '?__special_state__?'
        if self.parent.initial_animation == self.name:
            self.parent.initial_animation = None
        del self.parent.animation.states[self.name]
        del self.parent.animation.sequences[self.name]
        del self.parent.children[self.name]
        del self.parent.animation.objects['_gizmo_'].objects[self.name]
        
    def on_panel_show(self):
        try: self.parent.animation.state = self.name
        except: return
        
        self.panel.window.Bind(wx.EVT_TEXT, self.__on_fps_change, self.panel.fps)
        self.panel.window.Bind(wx.EVT_CHECKBOX, self.__on_checkbox)
        self.panel.window.Bind(wx.EVT_BUTTON, self.__on_stop, self.panel.stop)
        self.panel.window.Bind(wx.EVT_BUTTON, self.__on_play, self.panel.play)
        self.panel.window.Bind(wx.EVT_BUTTON, self.__on_apply, self.panel.apply)
        
        self.panel.fps.SetValue(self.fps)
        self.panel.looped.SetValue(self.looped)
        self.panel.vertical_flip.SetValue(self.vertical_flip)
        self.panel.horizontal_flip.SetValue(self.horizontal_flip)
        self.panel.reversed.SetValue(self.reversed)
        self.panel.ontimer.SetValue(self.ontimer)
        self.panel.period.Enable(self.ontimer)
        
        self.panel.islarge.SetValue(self.is_large_sequence)
        self.panel.iscomp.SetValue(self.is_compressed)
        
        if isinstance(self.period, list):
            self.panel.period.SetValue("%.1f-%.1f" % (self.period[0], self.period[1]))
        else:
            self.panel.period.SetValue(str(self.period))
        
        # Converting raw list of numbers to ranges
        i = 0
        s = []
        olddi = 0
        while i < len(self.frame_indices):
            if 0 == i: s.append([self.frame_indices[0]])
            else:
                di = self.frame_indices[i] - self.frame_indices[i-1]
                if abs(di) != 1 or (olddi != 0 and di != olddi):
                    if s[-1][0] != self.frame_indices[i-1]:
                        s[-1].append(self.frame_indices[i-1])
                    s.append([self.frame_indices[i]])
                    olddi = 0
                else: olddi = di
            i += 1
        if s[-1][0] != self.frame_indices[i-1]:
            s[-1].append(self.frame_indices[i-1])
        tokens = []
        for k in s:
            if len(k) == 2: tokens.append('%d-%d' % (k[0], k[1]))
            else: tokens.append('%d' % k[0])
        self.panel.sequence.SetValue(', '.join(tokens))
        self.__on_stop(None)
    
    def on_panel_hide(self):
        try:
            if self.parent.animation.sequences.has_key(self.name):
                self.parent.animation.sequences[self.name].play()
        except: return
        
        self.lock(True)
        self.fps = self.panel.fps.GetValue()
        self.horizontal_flip = self.panel.horizontal_flip.GetValue()
        self.vertical_flip = self.panel.vertical_flip.GetValue()
        self.looped = self.panel.looped.GetValue()
        self.reversed = self.panel.reversed.GetValue()
        self.ontimer = self.panel.ontimer.GetValue()
        self.is_large_sequence = self.panel.islarge.GetValue()
        self.is_compressed = self.panel.iscomp.GetValue()
        if self.ontimer:
            s = self.panel.period.GetValue().strip()
            
            try:
                self.period = float(s)
                if self.period <= 0:
                    self.ontimer = False
                    self.period = [3,5]
            except:
                try:
                    s = s.split('-')
                    self.period = [float(s[0].strip()), float(s[1].strip())]
                    if self.period[0] <= 0 or self.period[1] <= 0:
                        raise Error
                    if self.period[0] > self.period[1]:
                        self.period = list(reversed(self.period))
                    elif self.period[1] == self.period[0]:
                        self.period = self.period[1]
                except:
                    self.ontimer = False
                    self.period = [3,5]
    
    def lock(self, to_lock):
        if not to_lock and not self.tree.IsSelected(self.item): return
        ItemBase.lock(self, to_lock)
    
    def create_volatile_objects(self, parent):
        ''' Creating volatile objects after history shuffle '''
        
        self.panel_description = ['SEQUENCE_PROPS', {'fps'     : 'FPS_SLIDER',
                                                     'vertical_flip' : 'FLIP_VERTICAL',
                                                     'horizontal_flip' : 'FLIP_HORIZONTAL',
                                                     'looped'  : 'LOOPED',
                                                     'reversed': 'REVERSED',
                                                     'stop'    : 'STOP',
                                                     'play'    : 'PLAY',
                                                     'sequence': 'SEQUENCE',
                                                     'apply'   : 'APPLY',
                                                     'ontimer' : 'ONTIMER',
                                                     'period'  : 'PERIOD',
                                                     'islarge' : 'IS_LARGE',
                                                     'iscomp'  : 'IS_COMPRESSED'}]
        
        was_selected = getattr(self, 'item_is_selected', False)
        self.item_is_selected = False
        
        self.volatile_objects = ['gizmo']
        ItemBase.create_volatile_objects(self, parent)
        
        # Compatibility layer
        if not hasattr(self, 'original_path'): self.original_path = ''
        if not hasattr(self, 'ontimer'): self.ontimer = False
        if not hasattr(self, 'period'): self.period = [3, 5]
        if not hasattr(self, 'is_compressed'): self.is_compressed = True
        if not hasattr(self, 'horizontal_flip'): self.horizontal_flip = False
        if not hasattr(self, 'vertical_flip') : self.vertical_flip = False

        add_sequence = self.is_large_sequence and self.parent.animation.add_large_sound_sequence or \
                                                  self.parent.animation.add_sound_sequence
        try:
            add_sequence(self.name, self.animation_path, self.frame_indices, (), self.is_compressed)
        except:
            # Checking if file missing
            import os.path
            for i in self.frame_indices:
                if not os.path.exists(os.path.join(self.animation_path, '%d.png' % i)):
                    wx.MessageBox("Sequence frame file not found: %d.png" % i, "Error")
                    raise
            raise
        self.parent.animation.states[self.name] = Tanita2.State(self.name,
                                                      link=self.parent.link_function)
        
        self.parent.animation.sequences[self.name].position = \
            Tanita2.vec2(self.__position[0], self.__position[1])
        self.parent.animation.sequences[self.name].fps = self.fps
        self.parent.animation.sequences[self.name].horizontal_flip = self.horizontal_flip
        self.parent.animation.sequences[self.name].vertical_flip = self.vertical_flip
        self.parent.animation.sequences[self.name].looped = self.looped
        self.parent.animation.sequences[self.name].reversed = self.reversed
        
        bbox = self.parent.animation.sequences[self.name].bounding_box
        self.parent.animation.objects['_gizmo_'].objects[self.name] = \
            Gizmos.Gizmo(bbox.x, bbox.y, 0x7f75e880)
        self.gizmo = proxy(self.parent.animation.objects['_gizmo_'].objects[self.name])
        self.gizmo.position = Tanita2.vec2(self.__position[0], self.__position[1])
        
        if was_selected: self.tree.SelectItem(self.item)
        
    def __on_fps_change(self, event):
        new_fps = self.panel.fps.GetValue()
        if new_fps == self.fps: return
        
        self.track()
        self.fps = new_fps
        self.parent.animation.sequences[self.name].fps = self.fps
        
    def __on_checkbox(self, event):
        self.track()
        o = event.GetEventObject()
        if o == self.panel.looped:
            self.looped = self.panel.looped.GetValue()
        elif o == self.panel.reversed:
            self.reversed = self.panel.reversed.GetValue()
        elif o == self.panel.ontimer:
            self.ontimer = self.panel.ontimer.GetValue()
            self.panel.period.Enable(self.ontimer)
        elif o == self.panel.horizontal_flip:
            self.horizontal_flip = self.panel.horizontal_flip.GetValue()
        elif o == self.panel.vertical_flip:
            self.vertical_flip = self.panel.vertical_flip.GetValue()
        elif o == self.panel.iscomp:
            self.is_compressed = o.GetValue()
            self._update_item_order()
            return
        elif o == self.panel.islarge:
            self.is_large_sequence = o.GetValue()
            self._update_item_order()
            return
        
        self.parent.animation.sequences[self.name].vertical_flip = self.vertical_flip
        self.parent.animation.sequences[self.name].horizontal_flip = self.horizontal_flip
        self.parent.animation.sequences[self.name].looped = self.looped
        self.parent.animation.sequences[self.name].reversed = self.reversed
        
    def __on_stop(self, event):
        seq = self.parent.animation.sequences[self.name]
        seq.frame = 0
        self.parent.animation.sequences[self.name].stop()
        
    def __on_play(self, event):
        seq = self.parent.animation.sequences[self.name]
        seq.frame = 0
        seq.play()

    def __on_apply(self, event):
        f = self.panel.sequence.GetValue().split(',')
        
        frames = []
        try:
            for k in f:
                a = k.split('-')
                if len(a) == 2:
                    b = int(a[1])
                    a = int(a[0])
                    di = b - a > 0 and 1 or -1
                    frames.extend(list(xrange(a, b+di, di)))
                else: frames.append(int(a[0]))
        except: wx.MessageBox("Invalid image sequence.", "Error"); return
        if () == frames: wx.MessageBox("Image sequence is empty.", "Error"); return
        
        for i in frames:
            if not os.path.exists(os.path.join(self.animation_path, '%d.png' % i)):
                wx.MessageBox("Sequence frame doesn't exist: %d.png" % i, "Error")
                return
        self.track()
        self.frame_indices = tuple(frames)
        self._update_item_order()
        
    def _get_seq(self):
        return self.parent.animation.sequences[self.name]
    
    def check(self): pass

    def __topower2(self, n):
        x = 2
        while n > x: x <<= 1
        return x
