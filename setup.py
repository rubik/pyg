import os
import sys
import pyg

try:
    import setuptools
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()

from setuptools import setup


# Remove *.pyc files, since setuptools doesn't do that (even with the
# exclude_package_data keyword)
for dir, subdirs, files in os.walk(os.path.abspath('.')):
    for file in files:
        if file.endswith('.pyc'):
            os.remove(os.path.join(dir, file))

requires = ['setuptools', 'pkgtools>=0.7', 'argh']

if sys.version_info[:2] < (2, 7):
    requires.append('argparse>=1.2.1')

pyg_console_scripts = [
    'pyg = pyg:main',
    'pyg{0}.{1} = pyg:main'.format(*sys.version_info[:2])
]

long_desc = '''Pyg
===

Pyg is a Python package manager that is meant to be an alternative to easy_install and Pip.
It can download, install, remove packages and more.
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
If you want, you can try it without installing it. Just download the Pyg Pack from http://pyg.readthedocs.org/en/latest/_downloads/pyg1.zip, unzip it and run it:

    $ python run_pyg.py --help

You can install, remove, bundle, create packs and much more!
Check it at http://pyg-installer.co.nr
'''

setup(name='pyg',
      version=pyg.__version__,
      url='http://pyg-installer.co.nr',
      download_url='http://pypi.python.org/pypi/pyg',
      license='MIT',
      author='Michele Lacchia & Fabien Devaux',
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
