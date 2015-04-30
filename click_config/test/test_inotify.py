from tornado import gen, concurrent
import click
import click_config
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

    watcher.add_listener(key, lambda *args: future.set_result(args))

    result = yield future
    raise gen.Return(result)


@click.command()
@click_config.wrap(module=Config, sections=('logger', 'mysql'), watch=True)
def main(watcher):
    """
    :type watcher: click_config.inotify.Watcher
    """
    watcher.io_loop.call_later(0.01, alter_yaml, 'a.yaml',
                               {'mysql': {'port': Config.mysql.port + 1, 'host': 'remotehost'}})
    section, key, value = watcher.io_loop.run_sync(lambda: wait_for_change(('mysql', 'port'), watcher))
    watcher.stop()
    alter_yaml('a.yaml', {'mysql': {'port': Config.mysql.port - 1, 'host': 'remotehost'}})
    assert (section, key) == ('mysql', 'port')
    assert value == Config.mysql.port == 667


def test():
    os.environ['CONF'] = sample('b.yaml')
    sys.argv = sys.argv[0:1] + ['--conf-mysql', 'host: localhost', '--conf', sample('a.yaml')]
    try:
        main()
    except SystemExit:
        pass


if __name__ == '__main__':
    test()
