import sys
import pyg

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup


requires = ['setuptools', 'pkgtools>=0.6.1', 'argh']
if sys.version_info[:2] < (2, 7):
    requires.append('argparse>=1.2.1')

pyg_console_scripts = [
    'pyg = pyg:main',
    'pyg{0}.{1} = pyg:main'.format(*sys.version_info[:2])
]

long_desc = '''Pyg
===

Pyg is a Python package manager that is meant to be an alternative to easy_install.
It can download, install, remove packages.
Pyg supports almost all package filetypes:

 * .tar.gz
 * .tgz
 * .tar.bz2
 * .zip
 * .egg
 * .exe
 * .msi
 * .pybundle
 * .pyb (an abbreviation for .pybundle)

Pyg can remove all packages, even those installed with pure-distutils install (``python setup.py install``).
'''

setup(name='pyg',
      version=pyg.__version__,
      url='http://pyg-installer.co.nr',
      download_url='http://pypi.python.org/pypi/pyg',
      license='MIT',
      author='Michele Lacchia & Alex Marcat',
      author_email='michelelacchia@gmail.com',
      maintainer='Michele Lacchia',
      maintainer_email='michelelacchia@gmail.com',
      description='Python Package Manager',
      long_description=long_desc,
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Build Tools'
      ],
      platforms='any',
      packages=['pyg'],
      include_package_data=True,
      keywords=['python', 'easy_install', 'pip', 'setuptools', 'package manager', \
                'command line', 'CLI'],
      install_requires=requires,
      provides=['pyg'],
      zip_safe=False,
      entry_points={
        'console_scripts': pyg_console_scripts
      }
      )
