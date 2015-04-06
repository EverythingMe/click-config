from __future__ import absolute_import
import click
import click_config

__author__ = 'bergundy'


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
@click_config.wrap(module=Config, keys=('logger', 'mysql'))
def main(log_level):
    assert log_level == 'WARN'
    assert Config.mysql.host == 'localhost'
    assert Config.mysql.port == 666
    assert Config.mysql.database == 'test'
    assert Config.mysql.timeout == 0.5


if __name__ == '__main__':
    import sys
    import os

    os.environ['CONF'] = 'samples/b.yaml'
    sys.argv = sys.argv[0:1] + ['--conf-mysql', 'host: localhost', '--conf', 'samples/a.yaml',
                                '--log-level', 'WARN']
    main()
