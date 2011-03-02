import pyg
from setuptools import setup, find_packages


long_desc = '''
Pyg is a Python package manager that is meant to be an alternative to Easy_Install.
'''

requires = ['argparse']
try:
    import argparse
except ImportError:
    pass
else:
    del requires[-1]

setup(name='pyg',
      version=pyg.__version_str__,
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Build Tools'
      ],
      platforms='all',
      packages=find_packages(),
      install_requires=requires,
      entry_points={
        'console_scripts': [
            'pyg = pyg_install:main'
        ]
      }
      )