"""
  Cythonize.py build_ext --inplace
  Cythonize.py clean

"""

from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize("*.py"))
