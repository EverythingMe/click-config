from contextlib import contextmanager
from tornado import gen, concurrent
import click
import click_config
from tornado.ioloop import TimeoutError
import yaml
import os
import sys

__author__ = 'bergundy'

sample = lambda f: os.path.join(os.path.dirname(__file__), 'samples', f)


class Config(object):
    class mysql(object):
        timeout = 0.5
        host = None
        port = None
        database = None

    class logger(object):
        level = 'INFO'


def alter_yaml(path, contents):
    with open(sample(path), 'w') as f:
        yaml.dump(contents, f)


@gen.coroutine
def wait_for_change(key, watcher):
    future = concurrent.Future()
    callback = lambda *args: future.set_result(args)
    watcher.add_listener(key, callback)
    result = yield future
    watcher.remove_listener(key, callback)
    raise gen.Return(result)


@contextmanager
def restoring_config(filename):
    with open(sample(filename)) as f:
        cfg = yaml.load(f)
    try:
        yield
    finally:
        alter_yaml(filename, cfg)



@click.command()
@click_config.wrap(module=Config, sections=('logger', 'mysql'), watch=True)
def waiter(watcher):
    """
    :type watcher: click_config.inotify.Watcher
    """
    originalPort = Config.mysql.port
    with restoring_config('a.yaml'):
        watcher.io_loop.call_later(0.01, alter_yaml, 'a.yaml',
                                   {'mysql': {'port': Config.mysql.port + 1, 'host': 'remotehost'}})
        section, key, value = watcher.io_loop.run_sync(lambda: wait_for_change(('mysql', 'port'), watcher))
        watcher.stop()
    assert (section, key) == ('mysql', 'port')
    assert value == Config.mysql.port == originalPort + 1


def test_b_before_a():
    os.environ['CONF'] = sample('b.yaml')
    sys.argv = sys.argv[0:1] + ['--conf-mysql', 'host: localhost', '--conf', sample('a.yaml')]
    try:
        waiter()
    except SystemExit:
        pass


@click.command()
@click.option('--expected-port', type=int, required=True)
@click_config.wrap(module=Config, sections=('logger', 'mysql'), watch=True)
def passer(watcher, expected_port):
    """
    :type watcher: click_config.inotify.Watcher
    """
    with restoring_config('a.yaml'):
        watcher.io_loop.call_later(0.01, alter_yaml, 'a.yaml',
                                   {'mysql': {'port': Config.mysql.port + 1, 'host': 'remotehost'}})
        try:
            watcher.io_loop.run_sync(lambda: wait_for_change(('mysql', 'port'), watcher), timeout=0.1)
        except TimeoutError:
            pass
        else:
            assert False, "TimeoutError should have been raised"

        watcher.stop()
    assert Config.mysql.port == expected_port


def test_a_before_b():
    os.environ['CONF'] = sample('a.yaml')
    sys.argv = sys.argv[0:1] + ['--conf-mysql', 'host: localhost', '--conf', sample('b.yaml'), '--expected-port', '777']
    try:
        passer()
    except SystemExit:
        pass


def test_overrides():
    os.environ['CONF'] = sample('a.yaml')
    sys.argv = sys.argv[0:1] + ['--conf-mysql', 'host: localhost\nport: 888', '--conf', sample('b.yaml'),
                                '--expected-port', '888']
    try:
        passer()
    except SystemExit:
        pass
