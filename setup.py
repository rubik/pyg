import sys
import pyg
from setuptools import setup, find_packages


requires = ['setuptools']
try:
    import argparse
except ImportError:
    requires.append('argparse')

long_desc = '''Pyg 
===

Pyg is a Python package manager that is meant to be an alternative to easy_install. 
It can download, install, remove packages. 
Pyg supports almost all package filetypes:

 * .tar.gz 
 * .tar.bz2 
 * .zip 
 * .egg 
 * .pybundle 
 * .pyb (an abbreviation for .pybundle)

Pyg can remove all packages, even those installed with pure-distutils install (``python setup.py install``).
'''

setup(name='pyg',
      version=pyg.__version__,
      url='http://pyg-installer.co.nr',
      download_url='http://pypi.python.org/pypi/pyg',
      license='MIT',
      author='Michele Lacchia',
      author_email='michelelacchia@gmail.com',
      description='Python Package Manager',
      long_description=long_desc,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Build Tools'
      ],
      platforms='any',
      packages=['pyg'],
      keywords=['python', 'easy_install', 'setuptools', 'package manager'],
      install_requires=requires,
      entry_points={
        'console_scripts': [
            'pyg = pyg:main'
        ]
      }
      )
