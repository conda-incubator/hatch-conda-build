try:
    from hatch_conda_build._version import version as __version__
except ImportError:  # pragma: nocover
    __version__ = "unknown"

__all__ = ["__version__"]
