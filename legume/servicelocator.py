# -*- coding: utf-8 -*-
# legume. Copyright 2009-2011 Dale Reidy. All rights reserved.
# See LICENSE for details.

__docformat__ = 'restructuredtext'

class _ServiceRegistration(object):
    def __init__(self, name, klass, kwargs={}):
        self.name = name
        self.klass = klass
        self.kwargs = kwargs

class ServiceLocator(object):
    def __init__(self):
        self._dependencies = {}

    def add(self, name, klass, kwargs={}):
        d = _ServiceRegistration(name, klass, kwargs)
        self._dependencies[name] = d
        return d

    def resolve(self, name, kwargs={}):
        if name not in self._dependencies:
            raise Exception('Oops')
        d = self._dependencies[name]
        if kwargs == {}:
            return d.klass(**d.kwargs)
        else:
            return d.klass(**kwargs)

service = ServiceLocator()
add = service.add
Service = service.resolve

