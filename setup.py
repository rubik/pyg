import pyg
from setuptools import setup, find_packages


long_desc = '''
Pyg is a Python package manager that is meant to be an alternative to easy_install.
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Build Tools'
      ],
      platforms='any',
      packages=['pyg'],
      keywords=['python', 'easy_install', 'setuptools', 'package manager'],
      install_requires=['setuptools'],
      entry_points={
        'console_scripts': [
            'pyg = pyg:main'
        ]
      }
      )