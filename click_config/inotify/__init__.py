from __future__ import print_function
from tornado import ioloop
# noinspection PyUnresolvedReferences
from .. import notify, _parse_files, _extract_files_from_paths

import pyinotify

__author__ = 'bergundy'


class Watcher(object):
    ALL = object()

    def __init__(self, paths_to_watch, io_loop=None):
        self.io_loop = io_loop or ioloop.IOLoop.current()
        self.manager = pyinotify.WatchManager()
        self.notifier = pyinotify.TornadoAsyncNotifier(self.manager, self.io_loop)
        self.paths_to_watch = paths_to_watch
        for path in self.paths_to_watch:
            self.watch_path(path)
        self.listeners = {}

    def stop(self):
        self.notifier.stop()

    def watch_path(self, path, mask=pyinotify.IN_CLOSE_WRITE):
        self.manager.add_watch(path, mask, self.on_path_change)

    def on_path_change(self, event):
        notify('on_path_change:', event)
        for f, sect, items in _parse_files(_extract_files_from_paths([event.path])):
            for k, v in items:
                for path in self.ALL, sect, (sect, k):
                    if path in self.listeners:
                        for listener in self.listeners[path]:
                            listener(sect, k, v)

    def add_listener(self, key, listener):
        """
        :type key: tuple(str, str) or tuple(basestring) or ALL
        """
        assert callable(listener)
        self.listeners.setdefault(key, set()).add(listener)

    def remove_listener(self, key, listener):
        """
        :type key: tuple(str, str) or str or ALL
        """
        if key in self.listeners:
            listeners = self.listeners[key]
            listeners.remove(listener)
            if not listeners:
                del self.listeners[key]
