"""
HyP3 plugin for InSAR processing with ISCE
"""

# NOTE: Python 3.8+ only
from importlib.metadata import PackageNotFoundError, version


try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed!
    # Install in editable/develop mode via (from the top of this repo):
    #    pip install -e .
    # Or, to just get the version number use:
    #    python setup.py --version
    pass
