"""
  cythonize.py build_ext --inplace
  cythonize.py clean

"""

from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize("*.py"))
