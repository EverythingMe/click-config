try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = [
    'six',
    'pyyaml',
    'click'
]

test_requirements = [
    'pytest'
]

setup(
    name='click-config',
    description='config parsing helper for click',
    author='Roey Berman',
    author_email='roey@everything.me',
    url='https://github.com/EverythingMe/click-config',
    version='1.1.1',
    packages=['click_config'],
    keywords=['click', 'config', 'yaml', 'ini', 'cli'],
    install_requires=requirements,
    tests_require=test_requirements
)
