from Tanita2 import *
import sys, Lib.Globals
import Lib.config
import weakref
from Overrides import Cursor as UserCursor

# Cursor types
CURSOR_NORMAL = 0
CURSOR_ACTIVE = 1
CURSOR_TAKE = 2
CURSOR_APPLY = 3
CURSOR_IGNORE = 4
CURSOR_GOTO = 5
CURSOR_TALK = 6


class Regions:
    def __init__(self):
        self.__enabled_groups = {}
        self.__disabled_groups = {}
        self.__regions = []
        self.__group_name = 'Default'


    def change_load_group(self, name):
        self.__group_name = name
        self.refresh()


    def append(self, region, priority):
        region = weakref.ref(region)
        name = self.__group_name
        if name in self.__disabled_groups:
            self.__disabled_groups[name].append((region, priority))
            return

        if name not in self.__enabled_groups:
            self.__enabled_groups[name] = []

        self.__enabled_groups[name].append((region, priority))
        self.refresh()


    def remove(self, region):
        self.refresh()
        for regions in self.__enabled_groups.itervalues():
            for ref, priority in regions:
                rgn = ref()
                if rgn == region:
                    regions.remove((ref, priority))
                    break
        for regions in self.__disabled_groups.itervalues():
            for ref, priority in regions:
                rgn = ref()
                if rgn == region:
                    regions.remove((ref, priority))
                    break
        self.refresh()


    def enable(self, groups):
        for name in list(self.__disabled_groups.iterkeys()):
            if name in groups:
                self.__enabled_groups[name] = list(self.__disabled_groups[name])
                del self.__disabled_groups[name]
        for name in list(self.__enabled_groups.iterkeys()):
            if name not in groups:
                self.__disabled_groups[name] = list(self.__enabled_groups[name])
                del self.__enabled_groups[name]
        self.refresh()


    def refresh(self):
        regions = {}
        for refs in self.__enabled_groups.itervalues():
            for ref, priority in refs:
                region = ref()
                if not region:
                    continue
                region.clear()
                if priority not in regions:
                    regions[priority] = []
                regions[priority].append(region)
        self.__regions = []
        keys = list(regions.iterkeys())
        keys.sort()
        for priority in keys:
            self.__regions.append((priority, regions[priority]))


    def backup(self):
        return list(self.__enabled_groups.iterkeys())


    def restore(self, buffer):
        names = list(buffer)

        for name in list(self.__enabled_groups.iterkeys()):
            if name not in names:
                self.__disabled_groups[name] = list(self.__enabled_groups[name])
                del self.__enabled_groups[name]

        for name in list(self.__disabled_groups.iterkeys()):
            if name in names:
                self.__enabled_groups[name] = list(self.__disabled_groups[name])
                del self.__disabled_groups[name]
        self.refresh()


    def clear(self, name):
        if name in self.__enabled_groups:
            del self.__enabled_groups[name]
        if name in self.__disabled_groups:
            del self.__disabled_groups[name]
        self.refresh()


    def __iter__(self):
        return iter(self.__regions)




class Cursor(UserCursor):
    def __init__(self):
        UserCursor.__init__(self)
        # List of regions
        self.__regions = Regions()

        # Буферы для сохранения включенных груп
        self.__backupBuffers = {}

        # Игнорирование правой кнопки мыши
        self.__ignore_right_click = False

        # Mouse button previous state
        self.__previously_pressed = [False, False, False]

        # Режим Wait
        self.__is_waiting = False

        # Cursor state names in order of CURSOR_xxx constants

        self.__cursor_states = \
        {
            'Blue' : ['Normal_krosh', 'Active_krosh', 'Take', 'Apply_krosh', 'Normal_krosh', 'Goto_krosh', 'Talk_krosh'],
            'Violet' : ['Normal_ezhik', 'Active_ezhik', 'Take', 'Apply_ezhik', 'Normal_ezhik', 'Goto_ezhik', 'Talk_ezhik'],
            'Menu' : ['Normal_menu', 'Active_menu']
        }
        self.set_color('Blue')


    def set_color(self, color):
        from Core import engine
        engine.cursor.color = color
        UserCursor.set_color(self, color)
        self.__current_states = self.__cursor_states[color]


    def enable(self):
        from Core import engine
        engine.cursor.is_disabled = False
        engine.cursor.is_enabled = True
        UserCursor.enable(self)


    def disable(self):
        from Core import engine
        engine.cursor.is_disabled = True
        engine.cursor.is_enabled = False
        UserCursor.disable(self)
        self.__regions.refresh()


    def change_load_group(self, name):
        self.__regions.change_load_group(name)


    def enable_groups(self, groups):
        self.__regions.enable(groups)


    def backup_groups(self, bufferName=None):
        if bufferName is None:
            bufferName = 'Default'
        self.__backupBuffers[bufferName] = self.__regions.backup()


    def restore_groups(self, bufferName=None):
        if bufferName is None:
            bufferName = 'Default'
        if bufferName in self.__backupBuffers:
            self.__regions.restore(self.__backupBuffers[bufferName])
            del self.__backupBuffers[bufferName]


    def clear_group(self, name):
        self.__regions.clear(name)


    def append(self, region, priority=0):
        '''
        Add region to list

        '''
        self.__regions.append(region, priority)


    def remove(self, region):
        '''
        Remove region from list

        '''
        self.__regions.remove(region)


    def ignore_right_click(self, flag):
        self.__ignore_right_click = flag


    def wait_enable(self, flag):
        from Core import engine
        engine.cursor.is_waiting = flag
        self.hide_sequence(flag)
        self.__is_waiting = flag


    def process_regions(self):
        '''
        Region update flags

        '''
        # Updating position
        self.position = vec2(Lib.Globals.cursor_position)

        # Mouse buttons handling
        pressed = [False, False, False]
        clicked, released = pressed[:], pressed[:]
        for i in xrange(3):
            pressed[i] = bool(Lib.Globals.mouse_buttons & (1 << i))

            if pressed[i]:
                clicked[i] = not self.__previously_pressed[i]
                released[i] = False
            else:
                released[i] = self.__previously_pressed[i]
                clicked[i] = False
        self.__previously_pressed = pressed

        next_state = CURSOR_NORMAL

        is_ignored = False

        clicked_item_regions = []
        waiting_regions = []

        for priority, regions in self.__regions:

            if is_ignored:
                for r in regions:
                    r.clear()
            else:
                for r in regions:
                    if self.__is_waiting:
                        if r.is_inside(self.cursor):
                            waiting_regions.append(r)
                        r.clear()
                        continue

                    r.process(self.cursor, clicked, pressed, released)

                    if self.get_sequence_name():
                        if r.over:
                            clicked_item_regions.append(r)
                            if r.cursor == CURSOR_APPLY:
                                next_state = CURSOR_APPLY
                        r.clear()
                        continue

                    if not clicked_item_regions and r.over:
                        if r.cursor == CURSOR_IGNORE:
                            is_ignored = True

                        if r.over and r.cursor not in (CURSOR_NORMAL, CURSOR_IGNORE):
                            next_state = r.cursor
                        continue


        self.cursor.state = (self.__is_waiting and ['Clock'] or [self.__current_states[next_state]]).pop()

        if is_ignored:
            clicked[0] = False

        if True not in clicked:
            return

        if self.__is_waiting:
            kwargs = {}
            kwargs['click'] = clicked[0]
            kwargs['rclick'] = clicked[1]
            kwargs['mclick'] = clicked[2]
            kwargs['regions'] = list(waiting_regions)
            from Core import messages
            messages.send_all('on_wait_click', **kwargs)
            return

        # Посылаем сообщение о правой кнопке в любом случае
        if not self.__ignore_right_click and clicked[1]:
            from Core import messages
            messages.send_all('on_click', click=False, rclick=clicked[1], mclick=False)

        if self.get_sequence_name():
            kwargs = {}
            kwargs['click'] = clicked[0]
            kwargs['rclick'] = clicked[1]
            kwargs['mclick'] = clicked[2]
            kwargs['name'] = self.get_sequence_name()
            kwargs['regions'] = list(clicked_item_regions)
            from Core import messages
            if not messages.send_all('on_item_click', **kwargs):
                self.onUnprocessedItemClick()
            return

        # Посылаем всем сообщение о необработанном клике (не над регионом)
        from Core import messages
        if next_state == CURSOR_NORMAL and not clicked[1]:
            messages.send_all('on_click', click=clicked[0], rclick=clicked[1], mclick=clicked[2])
