from Core import *

class CommonCharacter:
    '''
    Класс, реализующий поведение персонажа.
    Отвечает за перемещение персонажа, проигрывание развлекательных анимаций,
    поиск пути, выполнение команд.
    
    Класс-наследник может переопределить следующие функции для тонкой настройки поведения персонажа:
        def _getMovementStateAndSpeed(self, startAbsPos, endAbsPos, deltaX, deltaY, directionX, directionY)
        def _getTransitionalAnimations(self, animation1, animation2)
        def _checkStopOnFrame(self, animation, frame)
        def _getIdleAnimation(self, idleTime)
        def _finishInitialization(self)
        def isStunned(self)
        def _enterDialogState(self)
        def _exitDialogState(self)
        def _stayInDialog(self)
        def initializeLipsync(self)
    '''
    
    def construct(self):
        # Добавление в список объектов, поддерживающий z-регионы.
        import weakref, Globals
        Globals.z_region_client_refs.append(weakref.ref(self))
        self.is_inside_z_region = False
        
        # Метасостояние персонажа (логическое состояние, не привязанное к анимациям)
        self.__metastate = 'Stay'
        self.__prevMetastate = 'Stay'
        
        # Обнуляем все привязки к состояниям.
        backups = {}
        for key, state in self.states.iteritems():
            backups[key] = (state.on_enter, state.on_exit, state.on_update, state.link)
            state.on_enter, state.on_exit, state.on_update, state.link = None, None, None, None
        
        self.state = 'Stay'
        
        # Восстанавливаем привязки к состояниям.
        for key in backups.iterkeys():
            state = self.states[key]
            state.on_enter, state.on_exit, state.on_update, state.link = backups[key]
        
        
        # Очередь анимаций персонажа.
        self.__stateQueue = []
        
        # Скорость перемещения персонажа по умолчанию.
        self.__DEFAULT_MOVEMENT_SPEED = 220
        # Квадрат минимального расстояния, на которое персонаж начнет движение.
        self.__MOVE_THRESHOLD_SQUARE = 100
        
        # Время простоя, в секундах.
        self.__idleTime = 0
        # Координаты, по которым нужно проиграть анимацию.
        self.__targetPosition = None
        
        # Флаг диалога.
        self.__inDialog = False

        # Флаг игнорирования кликов мышью
        self.__ignoreClick = False
        
        # Завершение инициализации.
        self._finishInitialization()
        self.initializeLipsync()
        
        # Тень будет обновляться вручную.
        self.objShadow.manualUpdate = self.objShadow.update
        self.objShadow.update = lambda dt: None
        
        # Инициализация масштабирования персонажа.
        self.__initScaling()
        
    
    def is_busy(self):
        '''
        Возвращает True, если анимация персонажа не может быть прервана.
        '''
        return self.__metastate == 'Busy'
        
    
    def isStunned(self):
        '''
        Возвращает True, если персонаж не может быть управляем.
        '''
        return False
        
    
    def sendToAnywhere(self, point):
        '''
        Отправляет персонажа в заданную точку. Если путь в точку не найден,
        вычисляется путь в ближайшую к ней. Если и этот путь не найден, возращает False.
        '''
        if not self.__ignoreClick:
            return self.__sendTo(point, lambda: None, 'Stay', shouldCheckTargetPoint=False)
        
    
    def sendTo(self, point, callback=lambda: None, targetState='Stay'):
        '''
        Отправляет персонажа в заданную точку.
        Если путь в данную точку не найден, возращает False, иначе True
        Иначе если персонаж не занят, он начинает движение и, если оно не было прервано, в конечной
        точке вызывает callback (если задан) и переходит в состояние targetState.
        '''
        if self.__ignoreClick and targetState == 'Stay':
            # Возвращаем True для обмана зоны перемещения
            return True
        result = self.__sendTo(point, callback, targetState, shouldCheckTargetPoint=True)
        if targetState != 'Stay':
            # Сохраняем персонажа для обработки его треем
            import Core
            Core.triggers.working_character = self.name
        return result
        
    
    def stopMovement(self):
        '''
        Останавливает перемещение персонажа. Возвращает True, если движение успешно
        остановлено.
        '''
        if self.__ignoreClick or self.is_busy() or self.__metastate == 'Idle':
            return self.__metastate == 'Idle'
        
        self.__clearStateQueue()
        self.__setupTransitionToStayAndGo(self.state, 'Stay', lambda: None)
        self.__metastate = 'Stay'
        return True
        
    
    def playBadReaction(self, authorSound=None):
        '''
        Проигрывает анимацию реакции на неправильные действия.
        '''
        self.__playReaction('No', authorSound)
        
    
    def playGoodReaction(self, authorSound=None):
        '''
        Проигрывает анимацию радости для правильных действий.
        '''
        self.__playReaction('Yes', authorSound)



    def enterIgnoreState(self):
        '''
        Выключаем реакцию на клик курсора

        '''
        self.__ignoreClick = True


    def exitIgnoreState(self):
        '''
        Включаем реакцию на клик курсора

        '''
        self.__ignoreClick = False
        
    
    def _enterBusyState(self, stateName):
        '''
        Функция, вызываемая для входа в состояние выполнения действия.
        Выход из состояния производится вызовом _exitBusyState.
        Функция предназначена для проигрывания пользовательской анимации
        без прерывания анимациями простоя.
        '''
        self.__clearStateQueue()
        self.__metastate = 'Busy'
        self.state = stateName
        
    
    def _exitBusyState(self):
        '''
        Функция, вызываемая для выхода из состояние выполнения действия в состояние покоя.
        '''
        self.__metastate = 'Stay'
        self.state = 'Stay'
        self.__idleTime = 0
        
    
    def _enterDialogState(self):
        '''
        Функция, вызываемая системой диалогов перед началом диалога для
        приведения персонажа в состояние разговора (поворот к собеседнику).
        '''
        def link():
            if self.seqTurn_to_dialog.is_over:
                return 'Stay_dialog'
        self.stateTurn_to_dialog.link = link
        self._enterBusyState('Turn_to_dialog')
        self.__inDialog = True
        
    
    def _stayInDialog(self):
        '''
        Функция, вызываемая системой диалогов после окончания каждой реплики.
        '''
        self.state = 'Stay_dialog'
        
    
    def _exitDialogState(self):
        '''
        Функция, вызываемая системой диалогов после завершения беседы.
        '''
        def link():
            if self.seqTurn_from_dialog.is_over:
                self._exitBusyState()
        self.stateTurn_from_dialog.link = link
        self.state = 'Turn_from_dialog'
        self.__inDialog = False
        
    
    def __sendTo(self, point, callback, targetState, shouldCheckTargetPoint):
        '''
        Вспомогательная функция для вычисления пути в заданную точку.
        '''
        assert point
        if self.is_busy() and not self.__inDialog:
            return False
        
        # FIXME: Костыль пока нет нужной анимации для применения предметов на локации
        if targetState not in self.states.iterkeys():
#            print "***********************************************"
#            print "* UNKNOWN STATE %s " % targetState
#            print "***********************************************"
            return False
        
        import Core
        Core.messages.send('Tray', 'Hide')
        
        # Второй персонаж.
        second_char = Core.second_character
        if Core.triggers.current_character != self.name:
            second_char = Core.active_character
        
        # Ищем путь.
        scrollOffset = self.position - self.absolute_position
        
        # Вычисляем targetPosition
        self.__targetPosition = vec2(point.position)

        path = self.__getPath(point.absolute_position)
        if not isinstance(path, str) and shouldCheckTargetPoint:
            # Проверяем, до той ли точки вычислен путь.
            dp = path[len(path) - 1] - scrollOffset - point.absolute_position
            if dp.x * dp.x + dp.y * dp.y > self.__MOVE_THRESHOLD_SQUARE:
                path = 'NotFound'
        
        if isinstance(path, str):
            if path == 'TooShort':
                # Путь слишком короткий. Считаем, что мы уже пришли.
                self.__clearStateQueue()
                self.__setupTransitionToStayAndGo(self.state, targetState, callback)
                second_char.stopMovement()
                return True
            
            else:
                assert path == 'NotFound'
                
                # Путь не найден, проверяем, не мешает ли нам второй гаврик.
                second_char._enableBlockRegion(False)
                path = self.__getPath(point.absolute_position)
                second_char._enableBlockRegion(True)
                
                if not isinstance(path, str) and shouldCheckTargetPoint:
                    # Проверяем, до той ли точки вычислен путь.
                    dp = path[len(path) - 1] - scrollOffset - point.absolute_position
                    if dp.x * dp.x + dp.y * dp.y > self.__MOVE_THRESHOLD_SQUARE:
                        path = 'NotFound'
                
                if isinstance(path, str):
                    # Путь вновь не найден или слишком короткий.
                    if path == 'TooShort':
                        # Путь слишком короткий. Считаем, что мы уже пришли.
                        self.__clearStateQueue()
                        self.__setupTransitionToStayAndGo(self.state, targetState, callback)
                        second_char.stopMovement()
                        return True
                    else:
                        return False
                
                # Путь найден! Второй персонаж явно нам мешает. Проверяем, может ли он куда-либо отойти.
                # Сортируем safePoints по расстоянию до персонажа.
                points = list(Core.engine.safe_points.itervalues())
                absPos = second_char.absolute_position
                def dist(a):
                    delta = a.absolute_position - absPos
                    return delta.x * delta.x + delta.y * delta.y
                points.sort(key=dist)
                
                for targetPoint in points:
                    secondPath = second_char._findPath(targetPoint.absolute_position)
                    if not isinstance(secondPath, str):
                        dp = secondPath[len(secondPath) - 1] - scrollOffset - targetPoint.absolute_position
                        if dp.x * dp.x + dp.y * dp.y > self.__MOVE_THRESHOLD_SQUARE:
                            continue
                        if second_char.sendTo(targetPoint, callback=lambda: self.sendTo(point, callback, targetState)):
                            return True
                return False
        
        # Если путь не найден (в виде объекта Path), мы сюда не попадем.
        
        # Останавливаем второго персонажа.
        second_char.stopMovement()
        
        # Добавляем путь и объект-заглушку, к нему прикрепленный.
        from Tanita2 import GameObject
        self.objects['__path'] = path
        path.enable_hack = True
        path.dummy = GameObject()
        path.dummy.previousPosition = vec2(0, 0)
        path.attach(path.dummy)
        path.stop()
        path.delta = path[len(path)-1] - point.absolute_position
        
        # Ставим анимации разворота и перемещения персонажа в очередь.
        walkOnEnter = lambda: path.play()
        walkOnExit = lambda: path.stop()
        transOnEnter = transOnExit = lambda: None
        transLink = lambda: self.sequences[self.state].is_over
        
        self.__clearStateQueue()
        for transitionAnimations, walkAnimation in path.keypointAnimations:
            # Для каждой анимации задаем функции, управляющие состоянием.
            for transitionAnimation in transitionAnimations:
                self.__stateQueue.append((transitionAnimation, transOnEnter, transOnExit, transLink))
            
            # Грязный хак. Пробовал по-другому (через lambda: keypoint.reached), но не работает.
            def walkLink():
                if not path.is_playing:
                    return not path.is_suspended
                for i, keypoint in enumerate(path.key_points.itervalues()):
                    if keypoint.reached and not path.reached_key_points[i]:
                        path.reached_key_points[i] = True
                        return True
            self.__stateQueue.append((walkAnimation, walkOnEnter, walkOnExit, walkLink))
        
        assert self.__stateQueue
        self.__setupTransitionToStayAndGo(self.__stateQueue[-1][0], targetState, callback)
        return True
        
    
    def update(self, dt):
        '''
        Обновление анимаций персонажа и переключение метасостояний.
        '''
        if self.is_inside_z_region:
            self.is_inside_z_region = False
            return
        
        # Отрисовываем тень раньше, чем персонажа.
        self.begin_update()
        self.objShadow.manualUpdate(dt)
        self.end_update()
        AnimatedObject.update(self, dt)
        
        # Обрабатываем масштабирование персонажа.
        self.__updateScaling()
        
        # Обрабатываем переходы между метасостояниями.
        if self.__prevMetastate != self.__metastate:
            if self.__metastate == 'Stay':
                # Сбрасываем время простоя.
                self.__idleTime = 0
            self.__prevMetastate = self.__metastate
        
        
        # Обрабатываем метасостояния.
        if self.__metastate == 'Go':
            # Перемещаем персонажа.
            path = self.objects['__path']
            deltaPos = path.dummy.position - path.dummy.previousPosition
            path.dummy.previousPosition = vec2(path.dummy.position)
            self.position += deltaPos
            
            # Приостанавливаем путь, если нужно для данного кадра.
            def suspend(flag):
                if path.is_suspended != flag:
                    path.is_suspended = flag
                    (path.play, path.stop)[int(flag)]()
            suspend(self._checkStopOnFrame(self.state, self.sequences[self.state].frame))
        
        elif self.__metastate == 'Stay':
            self.__idleTime += dt
            animation = self._getIdleAnimation(self.__idleTime)
            if animation is not None:
                def onExit():
                    self.__metastate = 'Stay'
                self.__stateQueue.append((animation, lambda: None, onExit,
                                          lambda: self.sequences[animation].is_over))
                def onEnter():
                    self.__metastate = 'Stay'
                    self.__idleTime = 0
                self.__stateQueue.append(('Stay', onEnter, lambda: None, lambda: True))
                self.__metastate = 'Idle'
                self.state = self.__stateQueue[0][0]
        
        
        # Обрабатываем очередь состояний.
        if self.__stateQueue:
            onExit, link = self.__stateQueue[0][2:]
            if link():
                # Меняем состояние
                onExit()
                del self.__stateQueue[0]
                if self.__stateQueue:
                    self.state, onEnter = self.__stateQueue[0][:2]
                    onEnter()
        
    
    def __clearStateQueue(self):
        '''
        Очищает очередь состояний персонажа: прерывает развлекательные анимации, отменяет перемещение.
        '''
        if self.__stateQueue:
            self.__stateQueue = []
        
        for sound in self.sounds.itervalues():
            sound.rewind()
        
    
    def _enableBlockRegion(self, enable):
        '''
        Включает/отключает блок-регионы персонажа.
        Эта функция не предназначена для перегрузки в классах-наследниках.
        '''
        import Core
        enableFunc = enable and (lambda x: x.enable()) or (lambda x: x.disable())
        map(enableFunc, (region for region in self.objects.itervalues()
                             if region.__class__ is Core.BlockRegion))
        
    
    def __getPath(self, targetAbsolutePosition):
        '''
        Вычисляет путь в заданную точку (в экранных координатах).
        Если путь не найден, возвращает строку с причиной, иначе возвращает объект типа Path,
        содержащий не менее 2х точек. Для каждой точки задана скорость движения и
        последовательность переключения анимаций походки (в поле path.keypointAnimations).
        
        Примечание: если путь в заданную точку не существует, возвращается максимально
        близкий к нему, если он может быть найден.
        '''
        path = self._findPath(targetAbsolutePosition)
        if isinstance(path, str):
            return path
        
        # Настраиваем ключевые точки пути.
        path.is_suspended = False
        previousPoint = vec2(path[0])
        path.keypointAnimations = []
        previousAnimation = self.state
        path.reached_key_points = []
        for i, point in enumerate(path.__iter__()[1:]):
            # Для каждой точки пути добавляем ключевую точку и запоминаем название анимации походки,
            # которая должна проигрываться на этом участке пути.
            delta = point - previousPoint
            deltaX, deltaY = int(delta.x), int(delta.y)
            
            directionX = int(deltaX > 0 or -(deltaX != 0)) # directionX = sign(deltaX)
            directionY = int(deltaY > 0 or -(deltaY != 0)) # sign(x) := {-1, x < 0; 0, x = 0; 1, x > 0}
            
            scrollOffset = self.position - self.absolute_position
            stateName, moveSpeed = self._getMovementStateAndSpeed(previousPoint - scrollOffset,
                                                                  point - scrollOffset,
                                                                  deltaX, deltaY, directionX, directionY)
            path.key_points[str(i)] = KeyPoint(i, moveSpeed)
            path.reached_key_points.append(0 == i)
            transitionAnimations = self._getTransitionalAnimations(previousAnimation, stateName)
            previousAnimation = stateName
            # Для каждой точки в path.keypointAnimations содержится список анимаций поворота и
            # анимация походки.
            path.keypointAnimations.append((transitionAnimations, stateName))
            previousPoint = vec2(point)
        return path
        
    
    def _findPath(self, targetAbsolutePosition):
        '''
        Вспомогательная функция для вычисления пути.
        Описание совпадает с описанием __getPath за тем исключением,
        что возвращаемый путь не имеет привязанных ключевых точек.
        '''
        import Globals
        
        # Отключаем собственный блок-регион (т.к. мы в нем находимся, путь будет найден неправильно), вычисляем путь.
        self._enableBlockRegion(False)
        path = Globals.walk_region_refs[0]().find_path(self.absolute_position, targetAbsolutePosition)
        self._enableBlockRegion(True)
        
        if len(path) < 2:
            return "NotFound"
        
        # Проверяем, что точки пути достаточно далеки друг от друга, чтобы избежать "дрожания" персонажа.
        if len(path) == 2:
            dx, dy = path[0].x - path[1].x, path[0].y - path[1].y
            if (dx * dx + dy * dy) < self.__MOVE_THRESHOLD_SQUARE:
                return "TooShort"
        return path
        
    
    def __setupTransitionToStayAndGo(self, fromState, targetState, callback):
        '''
        Вспомогательная функция, добавляющая в очередь анимаций перехож из fromState
        в анимацию покоя (targetState) с выполнением callback и запускающая проигрывание
        этой очереди.
        '''
        # Добавляем переход из последней фазы походки в Stay.
        transLink = lambda: self.sequences[self.state].is_over
        for transitionAnimation in self._getTransitionalAnimations(fromState, 'Stay'):
            self.__stateQueue.append((transitionAnimation, lambda: None, lambda: None, transLink))
        def stayOnEnter():
            self.__metastate = 'Stay'
            if targetState == 'Stay':
                callback()
        self.__stateQueue.append(('Stay', stayOnEnter, lambda: None, lambda: True))
        
        # Если задан targetState, переходим в него, а затем возвращаемся в Stay.
        if targetState != 'Stay':
            targetPosition = vec2(self.__targetPosition)
            def targetStateOnEnter():
                callback()
                self.__metastate = 'Busy'
                self.position = vec2(targetPosition)
            self.__stateQueue.append((targetState, targetStateOnEnter, lambda: None, transLink))
            def stayOnEnter():
                self.__metastate = 'Stay'
            self.__stateQueue.append(('Stay', stayOnEnter, lambda: None, lambda: True))
        
        # Переходим в состояние передвижения.
        self.__metastate = 'Go'
        self.state, onEnter = self.__stateQueue[0][:2]
        onEnter()
        
    
    def _getMovementStateAndSpeed(self, startAbsPos, endAbsPos, deltaX, deltaY, directionX, directionY):
        '''
        Возвращает tuple(название анимации походки для заданного направления, скорость перемещения)
        deltaX,Y - int, разница между координатами начала и конца отрезка пути.
        directionX,Y - int, направление перемещения по оси, -1, 0, 1.
        '''
        if deltaX * directionX > deltaY * directionY:
            return (('Goleft', '__wrong', 'Goright')[directionX + 1], self.__DEFAULT_MOVEMENT_SPEED)
        else:
            return (('Goback', '__wrong', 'Gofront')[directionY + 1], self.__DEFAULT_MOVEMENT_SPEED)
        
    
    def _getTransitionalAnimations(self, animation1, animation2):
        '''
        Возвращает tuple названий анимаций, которые надо проиграть для перехода из
        анимации 1 в анимацию 2.
        '''
        transitions = {
            'Stay'           : { 'Goright' : ['Rotate_fr_r'],
                                 'Goleft'  : ['Rotate_fr_l'],
                                 'Goback'  : ['Rotate_fr_back'] },
            
            'Goback'         : { 'Gofront' : ['Rotate_back_fr'],
                                 'Goright' : ['Rotate_back_r'],
                                 'Goleft'  : ['Rotate_back_l'],
                                 'Stay'    : ['Rotate_back_fr'] },
            
            'Gofront'        : { 'Goright' : ['Rotate_fr_r'],
                                 'Goleft'  : ['Rotate_fr_l'],
                                 'Goback'  : ['Rotate_fr_back'] },
            
            'Goright'        : { 'Gofront' : ['Rotate_r_fr'],
                                 'Goback'  : ['Rotate_r_back'],
                                 'Goleft'  : ['Rotate_r_fr', 'Rotate_fr_l'],
                                 'Stay'    : ['Rotate_r_fr'] },
            
            'Goleft'         : { 'Gofront' : ['Rotate_l_fr'],
                                 'Goback'  : ['Rotate_l_back'],
                                 'Goright' : ['Rotate_l_fr', 'Rotate_fr_r'],
                                 'Stay'    : ['Rotate_l_fr'] },
            
            'Rotate_back_r'  : { 'Gofront' : ['Rotate_back_r', 'Rotate_r_fr'],
                                 'Goback'  : ['Rotate_r_back'],
                                 'Goright' : ['Rotate_back_r'],
                                 'Goleft'  : ['Rotate_back_r', 'Rotate_r_fr', 'Rotate_fr_l'] },
            
            'Rotate_back_l'  : { 'Gofront' : ['Rotate_back_l', 'Rotate_l_fr'],
                                 'Goback'  : ['Rotate_l_back'],
                                 'Goleft'  : ['Rotate_back_l'],
                                 'Goright' : ['Rotate_back_l', 'Rotate_l_fr', 'Rotate_fr_l'] },
            
            'Rotate_r_back'  : { 'Gofront' : ['Rotate_back_r', 'Rotate_r_fr'],
                                 'Goback'  : ['Rotate_r_back'],
                                 'Goright' : ['Rotate_back_r'],
                                 'Goleft'  : ['Rotate_r_back', 'Rotate_back_l'] },
            
            'Rotate_l_back'  : { 'Gofront' : ['Rotate_back_l', 'Rotate_l_fr'],
                                 'Goback'  : ['Rotate_l_back'],
                                 'Goleft'  : ['Rotate_back_l'],
                                 'Goright' : ['Rotate_l_back', 'Rotate_back_r'] },
            
            'Rotate_l_fr'    : { 'Goleft'  : ['Rotate_fr_l'],
                                 'Goright' : ['Rotate_fr_r'] },
            
            'Rotate_r_fr'    : { 'Goleft'  : ['Rotate_fr_l'],
                                 'Goright' : ['Rotate_fr_r'] },
            
            'Rotate_fr_l'    : { 'Goright' : ['Rotate_l_fr', 'Rotate_fr_r'] },
            
            'Rotate_fr_r'    : { 'Goleft'  : ['Rotate_r_fr', 'Rotate_fr_l'] },
        }
        if animation1 in transitions:
            targets = transitions[animation1]
            if animation2 in targets:
                return tuple(targets[animation2])
        return ()
        
    
    def __playReaction(self, name, authorSound):
        '''
        Проигрывает заданную анимацию реакции на события игры.
        '''
        if not self.is_busy():
            self.stopMovement()
            self.__targetPosition = vec2(self.position)
            self.__setupTransitionToStayAndGo(self.state, name, lambda: None)
            self.__metastate = 'Stay'
            if authorSound is not None:
                author = engine.current_location.name.lower() + '_author'
                phrases = [(author, 'play_sound', authorSound)]
                messages.send('Author', 'say', phrases)
        
    
    def __initScaling(self):
        '''
        Инициализирует систему обновления масштаба персонажа.
        '''
        self.scale = vec2(1, 1)
        self.__scales = []
        self.__scalePreviousY = 0
        for pointName, point in engine.points.__children__.iteritems():
            if pointName.startswith('Scale_'):
                self.__scales.append((int(pointName[len('Scale_'):]) / 100.0, point.position.y))
        self.__scales.sort(lambda x, y: cmp(x[0], y[0]))
        self.__updateScaling()
        
    
    def __updateScaling(self):
        '''
        Обновляет масштаб персонажа.
        '''
        y = self.position.y
        if y == self.__scalePreviousY:
            return
        self.__scalePreviousY = y
        for i in range(1, len(self.__scales)):
            if self.__scales[i - 1][1] < y < self.__scales[i][1]:
                min_s, min_y = self.__scales[i - 1]
                max_s, max_y = self.__scales[i]
                percent = (y - min_y) / (max_y - min_y)
                scale = min_s + (max_s - min_s) * percent
                self.scale = vec2(scale, scale)
                break
        
    
    def _getIdleAnimation(self, idleTime):
        '''
        Возвращает название очередной анимации простоя или None.
        '''
        return None
        
    
    def _checkStopOnFrame(self, animation, frame):
        '''
        Возвращает True, если перемещение персонажа должно быть приостановлено,
        когда анимация с именем animation проигрывает кадр с номером frame.
        '''
        return False
        
    
    def _finishInitialization(self):
        '''
        Вызывается при завершении инициализации персонажа.
        '''
        pass
        
    
    def initializeLipsync(self):
        '''
        Вызывается в конце инициализации персонажа для загрузки
        анимаций разговора.
        '''
        self.onLipsyncLoad(False)
        
    
    def _getMetastate(self):
        '''
        Возращает метасостояние персонажа.
        '''
        return self.__metastate
        

    def _setIncorrectHandlers(self, state, on_enter=None, on_exit=None):
        '''
        Установка обработчиков для состояния неправильного применения предмета
        '''
        on_enter = (on_enter is None and [lambda: None] or [on_enter]).pop()
        on_exit = (on_exit is None and [lambda: None] or [on_exit]).pop()
        self.states[state].on_enter = lambda: [callback() for callback in (on_enter, lambda: messages.send('Tray', 'begin_incorrect_apply'))]
        self.states[state].on_exit = lambda: [callback() for callback in (lambda: messages.send('Tray', 'end_incorrect_apply'), on_exit)]
