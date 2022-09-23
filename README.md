## What is this

A tool to edit the metadata of a PDF in an intuitive way, without going through the command line.

As far as I am aware, there is no way to literally 'edit' them, so it will create a new file with the edited metadata and the same file name, while renaming the original by appending ``'_backup'``, as a safety measure.

Files to edit can be selected through the menu, or by draggin and dropping onto the main window.

## Known issues

* The window does not shrink in height automatically when a new PDF with fewer metadata entries is opened.
* Opening multiple PDF files within the same session generates lots of warnings in the console. The program still functions correctly nonetheless.
* Catching some known errors could be addressed more appropriately (e.g. attempting to open a password-protected PDF, attempting to edit a file when the corresponding ``_backup`` already exists)
