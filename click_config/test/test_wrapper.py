from __future__ import absolute_import
import sys

import click
import click_config
import os


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


@click.command()
@click.option('--log-level', type=str)
@click_config.wrap(module=Config, sections=('logger', 'mysql'), watch=False)
def main(log_level):
    """
    :type watcher: click_config.inotify.Watcher
    """
    assert log_level == 'WARN'
    assert Config.mysql.host == 'localhost'
    assert Config.mysql.port == 666
    assert Config.mysql.database == 'test'
    assert Config.mysql.timeout == 0.5


def test():
    os.environ['CONF'] = sample('b.yaml')
    sys.argv = sys.argv[0:1] + ['--conf-mysql', 'host: localhost', '--conf', sample('a.yaml'),
                                '--log-level', 'WARN']
    try:
        main()
    except SystemExit:
        pass


if __name__ == '__main__':
    test()
