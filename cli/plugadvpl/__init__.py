"""plugadvpl — CLI Python para indexar fontes ADVPL/TLPP do Protheus.

Companheiro do plugin Claude Code de mesmo nome. Ver:
https://github.com/JoniPraia/plugadvpl
"""

try:
    from plugadvpl._version import __version__
except ImportError:
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
