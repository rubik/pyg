.. highlight:: python

:mod:`pyg.types` --- Pyg base classes
=====================================

.. module:: pyg.types
    :synopsis: Pyg base classes

.. moduleauthor:: Michele Lacchia <michelelacchia@gmail.com>
.. sectionauthor:: Michele Lacchia <michelelacchia@gmail.com>



.. data:: pyg.types.args_manager

    This object stores command-line options. You can use it like a standard Python dictionary. Currently, it holds these options:

        **deps (True)**: if True, install package dependencies
        **index_url** (http://pypi.python.org):  the Package Index Url

        **upgrade (False)**: if True, force a re-installation

        **egg_install_dir** (:data:`~pyg.locations.INSTALL_DIR`): the Egg installation directory

.. autoclass:: pyg.types.ReqSet

.. autoclass:: pyg.types.Version

.. autoclass:: pyg.types.Egg

.. autoclass:: pyg.types.Archive

.. autoclass:: pyg.types.Bundle