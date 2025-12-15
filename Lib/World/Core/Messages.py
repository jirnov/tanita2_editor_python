from weakref import ref


class Messages:
    def __init__(self):
        self.__silence = True
        self.__ignore_warning = True
        self.__delayed = []
        self.__forcibly_pool_name = None
        self.__pools = {}
        if self.__silence:
            self.__info = lambda string: None
        else:
            self.__info = self.__write_info
        if self.__silence and self.__ignore_warning:
            self.__warn = lambda string: None
        else:
            self.__warn = self.__write_warn


    def __write_info(self, string):
        print 'Messages system: %s' % string


    def __write_warn(self, string):
        print 'Messages system WARNING: %s' % string


    def register(self, recipient_id, recipient, pool_name=None):
        '''
        Register message recipient

        '''
        assert hasattr(recipient, 'on_message') and callable(recipient.on_message), "Recipient %s must have methond 'on_message(msg_id, *args, **kwargs)'" % (repr(recipient_id))

        if pool_name is None:
            pool_name = 'Default'
        if self.__forcibly_pool_name:
            pool_name = self.__forcibly_pool_name
        if pool_name not in self.__pools:
            self.__info('create new pool %s' % repr(pool_name))
            self.__pools[pool_name] = {}
        self.__info('register %s(%s) recipient' % (repr(recipient_id), repr(pool_name)))
        pool = self.__pools[pool_name]
        if recipient_id in pool:
            self.__warn('changed registered recipient %s(%s)' % (repr(recipient_id), repr(pool_name)))
        pool[recipient_id] = ref(recipient)
        self.__refresh_pool()


    def send(self, recipient_id, message_id, *args, **kwargs):
        '''
        Send message to recipient

        '''
        self.__info('send message %s for %s' % (repr(message_id), repr(recipient_id)))
        for pool_name, pool in self.__pools.iteritems():
            if recipient_id in pool:
                recipient = pool[recipient_id]()
                if not recipient:
                    self.__warn('recipient %s(%s) alredy deleted' % (repr(recipient_id), repr(pool_name)))
                    continue
                result = recipient.on_message(message_id, *args, **kwargs)
                if result is None:
                    self.__warn('unknown message %s was been send for %s(%s)' % (repr(message_id), repr(recipient_id), repr(pool_name)))
                return result
        self.__delayed.append((recipient_id, message_id, args, kwargs))
        self.__info('message %s was been moved to delayed pool' % repr(message_id))



    def send_all(self, message_id, *args, **kwargs):
        '''
        Send message for all recipients

        '''
        self.__info('send message %s for all' % repr(message_id))
        for pool_name, pool in self.__pools.iteritems():
            for recipient_id, recipient in pool.iteritems():
                recipient = recipient()
                if not recipient:
                    continue
                result = recipient.on_message(message_id, *args, **kwargs)
                if result is None:
                    continue
                else:
                    self.__info('message %s for all was been received for %s(%s)' % (repr(message_id), repr(recipient_id), repr(pool_name)))
                    return result
        self.__warn('unknown message %s was been send for all' % repr(message_id))



    def __refresh_pool(self):
        for recipient_id, message_id, args, kwargs in list(self.__delayed):
            for pool_name, pool in self.__pools.iteritems():
                if recipient_id in pool:
                    recipient = pool[recipient_id]()
                    if not recipient:
                        self.__warn('recipient %s(%s) alredy deleted' % (repr(recipient_id), repr(pool_name)))
                        break

                    self.__delayed.remove((recipient_id, message_id, args, kwargs))
                    self.__info('delayed message %s was been received for %s(%s)' % (repr(message_id), repr(recipient_id), repr(pool_name)))
                    result = recipient.on_message(message_id, *args, **kwargs)
                    if result is None:
                        self.__warn('unknown delayed message %s was been send for %s(%s)' % (repr(message_id), repr(recipient_id), repr(pool_name)))
                    break


    def has_key(self, recipient_id, pool_name=None):
        if pool_name is None:
            pool_name = 'Default'
        for pool in self.__pools.itervalues():
            if recipient_id in pool:
                return True


    def unregister(self, recipient_id, pool_name=None):
        if pool_name is None:
            pool_name = 'Default'

        self.__info('unregister %s(%s) recipient' % (repr(recipient_id), repr(pool_name)))

        if pool_name in self.__pools:
            pool = self.__pools[pool_name]
            if recipient_id in pool:
                del pool[recipient_id]
                return
        self.__warn('try to remove unregistered recipient %s(%s)' % (repr(recipient_id), repr(pool_name)))


    def clear(self, pool_name=None):
        '''
        Clear messages pool

        '''
        if pool_name is None:
            pool_name = 'Default'

        self.__info('clear messages pool %s' % repr(pool_name))
        self.__pools[pool_name] = {}


    def enable_forcibly_pool(self, pool_name):
        self.__info('enable forcibly pool %s' % repr(pool_name))
        self.__forcibly_pool_name = pool_name



    def disable_forcibly_pool(self):
        self.__info('disable forcibly pool')
        self.__forcibly_pool_name = None
