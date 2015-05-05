Python config parsing helper for [click](http://click.pocoo.org)

```click-config``` provides a decorator that takes a python object and overwrites its attributes with values passed into the program via command line arguments.


## Usage:

Create an entry point for your project (e.g: main.py):
```python
from __future__ import print_function
import click
import click_config


class config(object):
    class logger(object):
        level = 'INFO'

    class mysql(object):
        host = 'localhost'


@click.command()
@click_config.wrap(module=config, sections=('logger', 'mysql'))
def main():
    print('log level: {}, mysql host: {}'.format(
        config.logger.level,
        config.mysql.host
    ))


if __name__ == '__main__':
    main()
```

```bash
$ python main.py --help
Usage: main.py [OPTIONS]

Options:
  --conf-mysql TEXT
  --conf-logger TEXT
  -c, --conf PATH
  --help              Show this message and exit.
```

The ```click_config.wrap``` decorator creates options for each one of the ```sections```:
```bash
$ python main.py --conf-logger "level: WARN"
log level: WARN, mysql host: localhost
```

You can also use the ```--conf``` option to pass in yaml files:
```bash
$ echo "logger: {level: WARN}" > /tmp/logger.yaml
$ echo "mysql: {host: remotehost}" > /tmp/mysql.yaml
$ python main.py --conf /tmp/mysql.yaml --conf /tmp/logger.yaml
log level: WARN, mysql host: remotehost
```

You can also use conf.d style configurations and pass ```--conf``` to recursively traverse a directory
```bash
$ echo "logger: {level: WARN}" > /tmp/conf.d/logger.yaml
$ echo "mysql: {host: remotehost}" > /tmp/conf.d/mysql.yaml
$ python main.py --conf /tmp/conf.d
log level: WARN, mysql host: remotehost
```

Finally, you can use the ```CONF``` environment variable as an alternative to the ```--conf``` command line option, use ':' as the delimiter:
```bash
$ echo "logger: {level: WARN}" > /tmp/logger.yaml
$ echo "mysql: {host: remotehost}" > /tmp/mysql.yaml
$ CONF=/tmp/mysql.yaml:/tmp/logger.yaml python main.py
log level: WARN, mysql host: remotehost
```


## inotify support (ALPHA):

```click-config``` also supports watching files using ```inotify``` and ```tornado```.
To enable this feature you must install ```click-config``` with the ```inotify``` extra.
```bash
$ pip install 'click-config[inotify]'
```
To watch files simply invoke ```click_config.wrap()``` with ```watch=True```
The configuration module will automatically be updated when the files change.
When using this feature, the wrapped function will receive a ```watcher``` parameter which you can use to listen for key change events.

```python
def on_key_change(section, key, value):
    pass

@click.command()
@click_config.wrap(module=config, sections=('logger', 'mysql'), watch=True)
def main(watcher):
    watcher.add_listener(('mysql', 'host'), on_key_change)  # watch a specific key
    watcher.add_listener(('mysql', ), on_key_change)        # watch all keys in the 'mysql' section
    watcher.add_listener(watcher.ALL, on_key_change)        # watch all keys in all sections
    watcher.io_loop.start()
```


## NOTES:

* ```click-config``` will parse any file ending with ```.conf```, ```.ini```, ```.yml``` or ```.yaml```.
* ```.conf``` and ```.ini``` are loaded with ConfigParser
* ```.yml``` and ```.yaml``` are loaded with a yaml parser
* A configuration object must be modeled in a 2 level hierarchy like an ```.ini``` file, where keys are stored under a section.
