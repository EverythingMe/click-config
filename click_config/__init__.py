from __future__ import absolute_import, print_function

try:
    # PY2
    # noinspection PyUnresolvedReferences
    from ConfigParser import ConfigParser
except ImportError:
    # PY3
    # noinspection PyUnresolvedReferences
    from configparser import ConfigParser

from itertools import chain
from warnings import warn

import functools
import click
import yaml
import six
import ast
import sys
import os

__author__ = 'bergundy'
notify = functools.partial(print, file=sys.stderr)

DEFAULT_ENV_VAR = 'CONF'


def load_from_env(module, env_var=DEFAULT_ENV_VAR, watch=False):
    return Parser(module, _parse_env(env_var), env_var=env_var, watch=watch)


def wrap(fn=None, module=None, sections=(), env_var=DEFAULT_ENV_VAR, watch=False):
    if fn is None:
        return functools.partial(wrap, module=module, sections=sections, env_var=env_var, watch=watch)

    @functools.wraps(fn)
    def wrapper(conf, **kwargs):
        kwargs_to_forward = {k: v for k, v in six.iteritems(kwargs) if not k.startswith('conf_')}
        overrides = (_parse_arg(k, v) for k, v in six.iteritems(kwargs) if k.startswith('conf_') and v)
        parser = Parser(module, _parse_env(env_var) + conf, overrides, env_var, watch)
        if watch:
            kwargs_to_forward['watcher'] = parser.watcher

        return fn(**kwargs_to_forward)

    wrapper = click.option('-c', '--conf', multiple=True, type=click.Path(exists=True))(wrapper)

    for section in sections:
        wrapper = click.option('--conf-{}'.format(section), multiple=True, type=str)(wrapper)

    return wrapper


def flatten_dicts(dicts):
    base = {}
    for d in dicts:
        base.update(d)
    return base


def _parse_files(files):
    for f in files:
        loader = _get_loader(f)
        if loader is None:
            continue

        for section, items in iter(loader):
            yield f, section, items


def loadYAML(f):
    with open(f) as f:
        data = yaml.load(f)
        if isinstance(data, dict):
            for section, config in six.iteritems(data):
                if config and isinstance(config, dict):
                    yield section, six.iteritems(config)


def loadINI(f):
    parser = ConfigParser()
    parser.optionxform = str
    parser.read(f)
    for section in parser.sections():
        yield section, ((k, parse_value(v)) for k, v in parser.items(section, raw=True) if v != '')


def parse_value(value):
    # noinspection PyBroadException
    try:
        return ast.literal_eval(value)
    except Exception:
        return ast.literal_eval('"%s"' % value)


def _get_loader(f):
    if f.endswith('.yaml') or f.endswith('.yml'):
        return loadYAML(f)
    elif f.endswith('.conf') or f.endswith('.ini'):
        return loadINI(f)
    else:
        return None


def _extract_files_from_paths(paths):
    for path in paths:
        if os.path.isdir(path):
            for f in sorted(os.listdir(path)):
                yield os.path.join(path, f)
        else:
            yield path


def _parse_env(env_var):
    return tuple(filter(None, os.environ.get(env_var, '').split(':')))


def _parse_arg(k, v):
    return '<ARG>', k[5:], six.iteritems(flatten_dicts(map(yaml.load, v)))


class Parser(object):
    def __init__(self, module, paths, overrides=None, env_var=DEFAULT_ENV_VAR, watch=False):
        self.module = module
        self.env_var = env_var
        self.watch = watch
        self.config_paths = paths
        self.overrides = overrides or []

        self.reload()

        if self.watch:
            from .inotify import Watcher
            self.watcher = Watcher(self)
            self.watcher.add_listener(self.watcher.ALL, self._on_key_change)

    def reload(self):
        for f, sect, items in chain(_parse_files(_extract_files_from_paths(self.config_paths)), self.overrides):
            self._configure_section(f, sect, items)

    def _on_key_change(self, section, key, value):
        self._configure_section('<WATCHER>', section, [(key, value)])

    def _handle_missing_section(self, section, f):
        warn('No section "{}" in module "{}" originating in file: "{}"'.format(section, self.module, f))

    def _handle_missing_key(self, section, key, f):
        warn('No key "{}" in section "{}" in module "{}" originating in file: "{}"'
             .format(key, section, self.module, f))

    def _configure_section(self, f, section, items):
        target = getattr(self.module, section, None)
        if target is None:
            # silently ignore
            self._handle_missing_section(section, f)
        notify('Configuring section "{}" from "{}"'.format(section, f))
        for k, v in items:
            try:
                setattr(target, k, v)
            except AttributeError:
                self._handle_missing_key(section, k, f)
