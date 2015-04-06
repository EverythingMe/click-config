from __future__ import absolute_import, print_function
from ConfigParser import ConfigParser
from itertools import chain, groupby

import functools
from operator import itemgetter
import click
import yaml
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


def _parse_files(paths):
    for f in _extract_files_from_paths(paths):
        loader = _get_loader(f)
        if loader is None:
            continue

        for section, items in groupby(loader, key=itemgetter(0)):
            yield f, section, items


def loadYAML(f):
    with open(f) as f:
        data = yaml.load(f)
        if isinstance(data, dict):
            for section, config in data.iteritems():
                if isinstance(config, dict):
                    for k, v in config.iteritems():
                        yield section, k, v


def loadINI(f):
    parser = ConfigParser()
    parser.optionxform = str
    parser.read(f)
    for section in parser.sections():
        for k, v in parser.items(section, raw=True):
            if v != '':
                yield section, k, parse_value(v)


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
    notify('Configuring section "{}" from "{}"'.format(section, f))
    for item in items:
        _, k, v = item
        setattr(target, k, v)


def _parse_arg(k, v):
    section = '<ARG>'
    key = k[5:]
    items = flatten_dicts(map(yaml.load, v)).iteritems()
    return section, key, ((key, k, v) for k, v in items)


def wrap(fn=None, module=None, keys=(), env_var='CONF'):
    assert module is not None, "module cannot be None"
    if fn is None:
        return functools.partial(wrap, module=module, keys=keys, env_var=env_var)

    @functools.wraps(fn)
    def wrapper(conf, **kwargs):
        conf = _parse_env(env_var) + conf
        kwargs_to_forward = {k: v for k, v in kwargs.iteritems() if not k.startswith('conf_')}
        kwargs_for_config = (_parse_arg(k, v) for k, v in kwargs.iteritems() if k.startswith('conf_') and v)
        for f, section, items in chain(_parse_files(conf), kwargs_for_config):
            target = getattr(module, section, None)
            _configure_section(f, section, target, items)

        return fn(**kwargs_to_forward)

    wrapper = click.option('-c', '--conf', multiple=True, type=click.Path(exists=True))(wrapper)
    for key in keys:
        wrapper = click.option('--conf-{}'.format(key), multiple=True, type=str)(wrapper)

    return wrapper


def load_from_env(module, env_var='CONF'):
    assert module is not None, "module cannot be None"

    for f, section, items in _parse_files(_parse_env(env_var)):
        target = getattr(module, section, None)
        _configure_section(f, section, target, items)
