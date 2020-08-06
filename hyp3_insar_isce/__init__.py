"""HyP3 plugin for InSAR processing with ISCE"""

# FIXME: Python 3.8+ this should be `from importlib.metadata...`
from importlib_metadata import PackageNotFoundError, version


try:
    __version__ = version(__name__)
except PackageNotFoundError:
    print('package is not installed!\n'
          'Install in editable/develop mode via (from the top of this repo):\n'
          '   pip install -e .\n'
          'Or, to just get the version number use:\n'
          '   python setup.py --version')
