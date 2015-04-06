from __future__ import absolute_import
import click_config

__author__ = 'bergundy'


class Config(object):
    class mysql(object):
        timeout = 0.5
        host = None
        port = None
        database = None


def main():
    assert Config.mysql.host == 'remotehost'
    assert Config.mysql.port == 666
    assert Config.mysql.database == 'test'
    assert Config.mysql.timeout == 0.5


if __name__ == '__main__':
    import os

    os.environ['TEST_CONF'] = 'samples/b.yaml:samples/a.yaml'
    click_config.load_from_env(Config, 'TEST_CONF')
    main()
