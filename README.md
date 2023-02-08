# PDF-Metadata-Editor

A GUI to edit the metadata of a PDF in an intuitive way, without going through the command line.

The GUI is created using [PyQt6][pyqt]; the operations of reading/writing PDF files are performed via [PyPDF2][pypdf].

Files can be selected through the menu, or by dragging and dropping onto the main window.

The program does not actually 'edit' the metadata, but creates a new file with the edited metadata; the original file is given a `.bak` extension (or `.bak1`, `.bak2`, etc. in case of duplicates) as a safety measure. Future versions may add an option to not create backups.

The program allows to change basic document metadata (Document Information Dictionary); XMP metadata are not supported in the current version.

## Installation

If you are looking for a standalone executable, check the [releases page](https://github.com/Manitary/PDF-Metadata-Editor/releases) for executable bundles.
If there is no bundle for your operating system then follow the installation instructions below.
Note that for the semi-automatic installation method, you will need [Python3][py3] on your computer.

### Semi-automatic installation

The easiest installation method is by using `pip`, from the root folder of this repository:

       pip install .

(please note the command ends with a dot)
which will install all required dependencies and install a new `pdf-metadata-editor` command.

## Known issues

- When a new PDF is opened, the window only resize by expanding, if needed. This is particularly noticeable when opening files with a long name.

## Licence

GPLv3

[py3]: https://www.python.org/downloads/
[pypdf]: https://github.com/py-pdf/pypdf
[pyqt]: https://www.riverbankcomputing.com/software/pyqt/
