Pyg and config files
====================

During the initialization, Pyg looks for configurations file, it this order:

    * :file:`./pyg.conf`: a configuration file in the current working directory:
    * :file:`~/pyg.conf`: where ``~`` stands for your :envvar:`HOME` directory;
    * :file:`~/.pyg/pyg.conf`.