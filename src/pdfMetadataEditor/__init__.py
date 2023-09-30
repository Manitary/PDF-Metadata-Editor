"""
pdfMetadataEditor provides a GUI to edit the metadata of a PDF in an intuitive way.

After installing the package, the program can be launched with the command ``pdf-metadata-editor``
This is equivalent to running ``main()``

Dependencies: PyQt6, pypdf, pypdf[crypto]

For more information, see the repository at https://github.com/Manitary/PDF-Metadata-Editor.
"""

from .editor import MainWindow, MetadataPanel, main
from ._version import __version__

__all__ = ["__version__", "MetadataPanel", "MainWindow", "main"]
