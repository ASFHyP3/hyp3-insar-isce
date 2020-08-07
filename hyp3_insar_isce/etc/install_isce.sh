#!/usr/bin/env bash

set -e

# ISCE has additional build (only) dependancies
#conda install -c conda-forge -y gcc_linux-64 gxx_linux-64 gfortran_linux-64 cython scons openmotif-dev

# Do required environment manipulation for building ISCE
ln -s ${CONDA_PREFIX}/bin/cython ${CONDA_PREFIX}/bin/cython3

export ISCE_SRC_ROOT=${PWD}
mkdir -p ${ISCE_SRC_ROOT}/_scons ${ISCE_SRC_ROOT}/_build
export SCONS_CONFIG_DIR=${ISCE_SRC_ROOT}/_scons

# Get needed info from the conda environment
export CONDA_HOST_NAME=$($CC -dumpmachine)
# NOTE: Careful we don't conflict with any of python expected env. variables:
#       https://docs.python.org/3/using/cmdline.html#environment-variables
export PYTHON_SITE_PACKAGES=$(python -c "from sysconfig import get_paths; print(get_paths()['purelib'])")
export PYTHON_INCLUDE_DIR=$(python -c "from sysconfig import get_paths; print(get_paths()['include'])")
export NUMPY_INCLUDE_DIR=$(python -c "import numpy; print(numpy.get_include())")

echo '
# The directory in which ISCE will be built
PRJ_SCONS_BUILD = $ISCE_SRC_ROOT/_build/isce
# The directory into which ISCE will be installed
PRJ_SCONS_INSTALL = $PYTHON_SITE_PACKAGES/isce
# The location of libraries, such as libstdc++, libfftw3
LIBPATH = $CONDA_PREFIX/$CONDA_HOST_NAME/lib $CONDA_PREFIX/lib
# The location of Python.h. If you have multiple installations of python
# make sure that it points to the right one
CPPPATH = $PYTHON_INCLUDE_DIR $NUMPY_INCLUDE_DIR $CONDA_PREFIX/include
# The location of the fftw3.h
FORTRANPATH =  $CONDA_PREFIX/include
# The location of your Fortran compiler. If not specified it will use the system one
FORTRAN = $FC
# The location of your C compiler. If not specified it will use the system one
CC = $CC
# The location of your C++ compiler. If not specified it will use the system one
CXX = $CXX
# Libraries needed for mdx display utility
MOTIFLIBPATH = $CONDA_PREFIX/lib       # path to libXm.dylib
X11LIBPATH = $CONDA_PREFIX/lib         # path to libXt.dylib
MOTIFINCPATH = $CONDA_PREFIX/include   # path to location of the Xm
                                         # directory with various include files (.h)
X11INCPATH = $CONDA_PREFIX/include     # path to location of the X11 directory
                                         # with various include files
# Explicitly enable cuda if needed
# ENABLE_CUDA = False
' > _scons/SConfigISCE

scons install > >(tee -a _scons/scons.out) 2> >(tee -a _scons/scons.err >&2)

cp -r _build/isce/* ${PYTHON_SITE_PACKAGES}/isce/

# Finalize our conda env. by removing the ISCE build (only) dependancies
conda remove -y gcc_linux-64 gxx_linux-64 gfortran_linux-64 cython scons openmotif-dev

conda env config vars set ISCE_HOME=${PYTHON_SITE_PACKAGES}/isce
conda env config vars set PATH=${PATH}:${PYTHON_SITE_PACKAGES}/isce/bin:${PYTHON_SITE_PACKAGES}/isce/applications

conda clean -afy
