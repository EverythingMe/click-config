try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requirements = [
    'pyyaml',
    'click'
]

setup(
    name='click-config',
    description='config parsing helper for click',
    author='Roey Berman',
    version='1.0',
    packages=['click_config'],
    install_requires=requirements
)
