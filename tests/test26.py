#!/usr/bin/env python2.6
import os
from compileall import compile_dir

src_dir = os.path.join(os.path.pardir, 'pyg')

for root, dirs, files in os.walk(src_dir):
    for fname in files:
        if fname.endswith('.pyc') or fname.endswith('.pyo'):
            os.unlink( os.path.join(root, fname) )

compile_dir(src_dir)

