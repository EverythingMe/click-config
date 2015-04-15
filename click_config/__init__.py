from __future__ import absolute_import, print_function

try:
    # PY2
    # noinspection PyUnresolvedReferences
    from ConfigParser import ConfigParser
except ImportError:
    # PY3
    # noinspection PyUnresolvedReferences
    from configparser import ConfigParser

from itertools import chain, groupby

import functools
from operator import itemgetter
import click
import yaml
import six
import ast
import sys
import os

__author__ = 'bergundy'
notify = functools.partial(print, file=sys.stderr)


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

        for section, items in loader:
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
            for f in os.listdir(path):
                yield os.path.join(path, f)
        else:
            yield path


def _parse_env(env_var):
    return tuple(filter(None, os.environ.get(env_var, '').split(':')))


def _configure_section(f, section, target, items):
    if target is None:
        # silently ignore
        return
    notify('Configuring section "{}" from "{}"'.format(section, f))
    for k, v in items:
        setattr(target, k, v)


def _parse_arg(k, v):
    return '<ARG>', k[5:], six.iteritems(flatten_dicts(map(yaml.load, v)))


def on_key_change(module, section, key, value):
    target = getattr(module, section, None)
    _configure_section('<WATCHER>', section, target, [(key, value)])


def wrap(fn=None, module=None, sections=(), env_var='CONF', watch=False):
    assert module is not None, "module cannot be None"
    if fn is None:
        return functools.partial(wrap, module=module, sections=sections, env_var=env_var, watch=watch)

    @functools.wraps(fn)
    def wrapper(conf, **kwargs):
        conf = _parse_env(env_var) + conf
        kwargs_to_forward = {k: v for k, v in six.iteritems(kwargs) if not k.startswith('conf_')}
        kwargs_for_config = (_parse_arg(k, v) for k, v in six.iteritems(kwargs) if k.startswith('conf_') and v)

        for f, sect, items in chain(_parse_files(_extract_files_from_paths(conf)), kwargs_for_config):
            target = getattr(module, sect, None)
            _configure_section(f, sect, target, items)

        if watch:
            from .inotify import Watcher
            kwargs_to_forward['watcher'] = watcher = Watcher(conf)
            watcher.add_listener(watcher.ALL, functools.partial(on_key_change, module))

        return fn(**kwargs_to_forward)

    wrapper = click.option('-c', '--conf', multiple=True, type=click.Path(exists=True))(wrapper)
    for section in sections:
        wrapper = click.option('--conf-{}'.format(section), multiple=True, type=str)(wrapper)

    return wrapper


def load_from_env(module, env_var='CONF'):
    assert module is not None, "module cannot be None"

    for f, section, items in _parse_files(_parse_env(env_var)):
        target = getattr(module, section, None)
        _configure_section(f, section, target, items)
