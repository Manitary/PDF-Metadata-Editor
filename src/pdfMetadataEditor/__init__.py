"""
pdfMetadataEditor provides a GUI to edit the metadata of a PDF in an intuitive way.

After installing the package, the program can be launched with the command ``pdf-metadata-editor``
This is equivalent to running ``main()``

Dependencies: PyQt6, PyPDF2, PyPDF2[crypto]

For more information, see the repository at https://github.com/Manitary/PDF-Metadata-Editor.
"""

from .editor import MainWindow, TagData, MetadataPanel, main
from ._version import __version__

__all__ = ["__version__", "TagData", "MetadataPanel", "MainWindow", "main"]
