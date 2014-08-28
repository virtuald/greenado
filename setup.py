#!/usr/bin/env python

from os.path import join, dirname
from distutils.core import setup

setup_dir = dirname(__file__)
exec(compile(open(join(setup_dir, 'greenado', 'version.py')).read(), 'version.py', 'exec'), {}, globals())        


setup(
    name='greenado',
    version=__version__,
    description='Greenlet-based coroutines for tornado',
    long_description=open(join(setup_dir, 'README.rst')).read(),
    author='Dustin Spicuzza',
    author_email='dustin@virtualroadside.com',
    license="Apache 2.0",
    url='https://github.com/virtuald/greenado',
    packages=['greenado'],
    install_requires=['greenlet', 'tornado'],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
