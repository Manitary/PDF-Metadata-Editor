# PDF-Metadata-Editor

A tool to edit the metadata of a PDF in an intuitive way, without going through the command line.

As far as I am aware, there is no way to literally 'edit' them, so it will create a new file with the edited metadata and the same file name, while renaming the original by appending ``'_backup'``, as a safety measure.

Files to edit can be selected through the menu, or by draggin and dropping onto the main window.

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

* The window does not shrink in height automatically when a new PDF with fewer metadata entries is opened.
* Opening multiple PDF files within the same session generates lots of warnings in the console. The program still functions correctly nonetheless.
* Catching some known errors could be addressed more appropriately (e.g. attempting to open a password-protected PDF, attempting to edit a file when the corresponding ``_backup`` already exists)

## Licence

GPLv3

[py3]: https://www.python.org/downloads/
