"""Strip outputs and noisy metadata from Jupyter notebooks."""
from .core import clean_notebook, is_clean, scan_secrets

__version__ = "0.1.0"
__all__ = ["clean_notebook", "is_clean", "scan_secrets"]
