import sys
from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
from pathlib import Path

try:
    dist_name = "Z-model"
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    version_file = (Path.cwd() / __file__).with_name('data') / 'version'
    if version_file.exists():
        with open(version_file, 'r') as f:
            __version__ = f.read()
    else:
        __version__ = "unknown"
finally:
    del version, PackageNotFoundError
