from importlib.metadata import PackageNotFoundError, version

from loguru import logger

try:
    if isinstance(__package__, str):
        __version__ = version(__package__)
    else:
        __version__ = "unknown"
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"


logger.disable("diff_paths")
logger.remove()
