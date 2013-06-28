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

requires = ['setuptools', 'pkgtools>=0.7.1', 'argh']
if sys.version_info[:2] < (2, 7):
    requires.append('argparse>=1.2.1')

pyg_console_scripts = [
    'pyg = pyg:main',
    'pyg{0}.{1} = pyg:main'.format(*sys.version_info[:2])
]

if '--single-exe' in sys.argv:
    del pyg_console_scripts[0]
    sys.argv.remove('--single-exe')

with open('README.rst') as f:
    long_desc = f.read()


setup(name='pyg',
      version=pyg.__version__,
      url='http://pyg.readthedocs.org/',
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

