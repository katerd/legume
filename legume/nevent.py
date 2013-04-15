# -*- coding: utf-8 -*-
# legume. Copyright 2009-2013 Dale Reidy. All rights reserved.
# See LICENSE for details.
#
# ---------
#
# WeakMethod
#
# By J Knapka
# http://code.activestate.com/recipes/81253/
# Released under the PSF License
#

__docformat__ = 'restructuredtext'

from weakref import ref

def isbound(method):
    try:
        return method.im_self is not None
    except AttributeError:
        return False

def instance(bounded_method):
    return bounded_method.im_self

# ####################

class _weak_callable(object):
    __slots__ = ['_obj', '_meth']

    def __init__(self,obj,func):
        self._obj = obj
        self._meth = func

    def __call__(self,*args,**kws):
        if self._obj is not None:
            return self._meth(self._obj,*args,**kws)
        else:
            return self._meth(*args,**kws)

    def __getattr__(self,attr):
        if attr == 'im_self':
            return self._obj
        if attr == 'im_func':
            return self._meth
        raise AttributeError(attr)

    def __cmp__(self, other):
        return (other._obj == self._obj) and (self._meth == other._meth)

    def compare_method(self, method):
        if isbound(method):
            return method.im_self == self._obj and method.im_func == self._meth
        else:
            return method == self._meth

class WeakMethod(object):
    '''Wraps a function or, more importantly, a bound method, in
    a way that allows a bound method's object to be GC'd, while
    providing the same interface as a normal weak reference.'''

    __slots__ = ['_obj', '_meth']

    def __init__(self,fn):
        try:
            self._obj = ref(fn.im_self)
            self._meth = fn.im_func
        except AttributeError:
            # It's not a bound method.
            self._obj = None
            self._meth = fn

    def __call__(self):
        if self._dead(): return None

        if self._obj is None:
            # if _obj is None this is an unbound method.
            return _weak_callable(None, self._meth)
        else:
            return _weak_callable(self._obj(),self._meth)

    def _dead(self):
        return self._obj is not None and self._obj() is None

# ####################

class NEventError(Exception): pass

class Event(object):
    def __init__(self):
        self._handlers = []

    def __iadd__(self, other):
        if not self.is_handled_by(other):
            self._handlers.append(WeakMethod(other))
        else:
            raise NEventError('Event %s error: Handler %s is already bound' % (self, other))
        return self

    def __isub__(self, other):
        try:
            self._handlers = \
                [h for h in self._handlers
                 if h() and not h().compare_method(other)]
        except IndexError:
            raise (NEventError, 'Event %s error: Handler %s is not bound' % (self, other))
        return self

    def __call__(self, sender, args):
        self._handlers = [h for h in self._handlers if h()]

        result = None
        for handler in self._handlers:
            result = handler()(sender, args)
        return result

    def is_handled_by(self, handler):
        if isbound(handler):
            return handler.im_func in [h()._meth for h in self._handlers]
        else:
            return handler in [h()._meth for h in self._handlers]