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


def test():
    import os
    sample = lambda f: os.path.join(os.path.dirname(__file__), 'samples', f)

    os.environ['TEST_CONF'] = ':'.join([sample('b.yaml'), sample('a.yaml')])
    click_config.load_from_env(Config, 'TEST_CONF')
    main()


if __name__ == '__main__':
    test()
