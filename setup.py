try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = [
    'six',
    'pyyaml',
    'click',
    'fn'
]

test_requirements = [
    'pytest'
]

inotify_requirements = [
    'pyinotify',
    'tornado'
]

setup(
    name='click-config',
    description='config parsing helper for click',
    author='Roey Berman',
    author_email='roey@everything.me',
    url='https://github.com/EverythingMe/click-config',
    version='1.2.0',
    packages=['click_config'],
    keywords=['click', 'config', 'yaml', 'ini', 'cli'],
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require={
        'inotify': inotify_requirements
    }
)
