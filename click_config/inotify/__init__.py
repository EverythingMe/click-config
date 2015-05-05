from __future__ import print_function
from collections import defaultdict
from itertools import chain, ifilter
from fn.iters import accumulate
from tornado import ioloop
from .. import notify, _parse_files, _extract_files_from_paths
from .layers import LayerDict

import pyinotify
import os

__author__ = 'bergundy'


class Watcher(object):
    ALL = object()

    def __init__(self, parser, io_loop=None):
        """
        :type parser: click_config.Parser
        """
        self.io_loop = io_loop or ioloop.IOLoop.current()
        self.manager = pyinotify.WatchManager()
        self.notifier = pyinotify.TornadoAsyncNotifier(self.manager, self.io_loop)
        self.absolute_paths = [os.path.abspath(p) for p in parser.config_paths]
        self._sections = defaultdict(LayerDict)

        for i, path in enumerate(self.absolute_paths):
            self.watch_path(path)
        self.listeners = {}

        configs = [_parse_files(_extract_files_from_paths([path])) for path in self.absolute_paths]
        for i, gen in enumerate(chain(configs, parser.overrides)):
            for f, sect, items in gen:
                self._sections[sect].set_layer((i, f), dict(items))

    def stop(self):
        self.notifier.stop()

    def watch_path(self, path, mask=pyinotify.IN_CLOSE_WRITE):
        self.manager.add_watch(path, mask, self.on_path_change)

    def on_path_change(self, event):
        notify('on_path_change:', event)
        event_path = os.path.abspath(event.path)
        nodes = {'/' + p for p in accumulate(event_path.split(os.sep),
                                             lambda acc, x: os.path.join(acc, x))}

        indices_to_paths = enumerate(os.path.abspath(p) for p in self.absolute_paths)
        index, _ = next(ifilter(lambda (i, p): p in nodes, indices_to_paths))

        for f, sect, items in _parse_files(_extract_files_from_paths([event_path])):
            changes = self._sections[sect].set_layer((index, event_path), dict(items))
            for k, v in changes.iteritems():
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
