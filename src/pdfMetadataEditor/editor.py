"""This module provides a GUI to intuitively edit the metadata of a PDF.

Methods
-------
    main : Launch the GUI.

Classes
-------
    MainWindow : Handle the main window of the application.
    MetadataPanel : Handle the central widget of the main window.
        It is effectively the interface through which the user modifies the metadata.
    TagData : Contain all the objects related to a metadata field:
        its value, the GUI elements to modify it, the associated signals."""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass
from collections import defaultdict
import PyPDF2
from PyQt6 import QtWidgets, QtGui, QtCore
from PyPDF2.errors import PdfReadError
from ._version import __version__

APPLICATION_NAME = "PDF Metadata Editor"
URL_GITHUB = "https://github.com/Manitary/PDF-Metadata-Editor"

TAGS = ["/Title", "/Author", "/Subject", "/Keywords", "/Producer", "/Creator"]

BG_DEFAULT = QtCore.Qt.GlobalColor.white
BG_HIGHLIGHT = QtCore.Qt.GlobalColor.red


@dataclass
class TagData:
    """A class that handles the objects associated to a tag.

    Attributes
    ----------
    value : str
        The metadata value.
    line_edit : QLineEdit
        The widget to display and modify the value.
    reset_button : QPushButton
        The button to reset the QLineEdit text.
    reset_function : Callable
        The slot called when ``reset_button`` is pressed.
    save_function : Callable
        The function called to save the ``line_edit`` text as new ``value``.
    modified : bool
        True if the ``line_edit`` text differs from ``value``.
    interactive : bool
        True if the ``line_edit`` text can be edited by the user.

    Methods
    -------
    from_metadata_interactive(value="")
        Create a TagData object with the given value and an interactive ``line_edit``.
    from_metadata_not_interactive(value="")
        Create a TagData object with the given value and a non-interactive ``line_edit``.
    change_widget_background_colour(widget, colour)
        Change the background colour of ``widget`` to ``colour``.
    """

    value: str = ""
    line_edit: QtWidgets.QLineEdit = None
    reset_button: Optional[QtWidgets.QPushButton] = lambda: None
    reset_function: Optional[Callable[[None], None]] = lambda: None
    save_function: Optional[Callable[[None], None]] = lambda: None
    modified: bool = False
    interactive: bool = False

    @classmethod
    def from_metadata_interactive(cls, value: str = "") -> TagData:
        """Create a TagData object with an interactive ``line_edit``.

        Parameters
        ----------
        value : str
            The value of the metadata.
        """
        tag = TagData(value=str(value))
        line_edit = QtWidgets.QLineEdit(value)
        reset_button = QtWidgets.QPushButton("Reset")

        def reset_function() -> None:
            """Reset the text of ``line_edit`` to ``value``.

            It is the slot called when reset_button is pressed."""
            line_edit.setText(tag.value)

        def save_function() -> None:
            """Set ``value`` to the text of ``line_edit``.

            Additionally, set ``modified`` to False, and reset ``line_edit`` background colour.
            It is called when the "Save" button is pressed."""
            tag.modified = False
            tag.value = line_edit.text()
            TagData.change_widget_background_colour(line_edit, BG_DEFAULT)

        def edit_function() -> None:
            """Update ``modified`` and ``line_edit`` background colour based on its text.

            It is the slot called when ``line_edit`` text is changed."""
            if line_edit.text() == value:
                tag.modified = False
                TagData.change_widget_background_colour(line_edit, BG_DEFAULT)
            else:
                tag.modified = True
                TagData.change_widget_background_colour(line_edit, BG_HIGHLIGHT)

        line_edit.textChanged.connect(edit_function)
        reset_button.clicked.connect(reset_function)

        tag.line_edit = line_edit
        tag.reset_button = reset_button
        tag.reset_function = reset_function
        tag.save_function = save_function
        tag.interactive = True
        return tag

    @classmethod
    def from_metadata_not_interactive(cls, value: str = "") -> TagData:
        """Create a TagData object with an non-interactive ``line_edit``.

        Parameters
        ----------
        value : str
            The value of the metadata.
        """
        line_edit = QtWidgets.QLineEdit(str(value))
        line_edit.setEnabled(False)
        return TagData(value=value, line_edit=line_edit)

    @staticmethod
    def change_widget_background_colour(
        widget: QtWidgets.QWidget, colour: QtCore.Qt.GlobalColor
    ) -> None:
        """Change a widget background colour to the assigned colour.

        Currently only accepts PyQt pre-set colours.

        Parameters
        ----------
        widget : QWidget
            The widget to modify.
        colour : GlobalColor
            A PyQt pre-set colour.
            See complete list at https://doc.qt.io/qt-6/qt.html#GlobalColor-enum.
        """
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(colour))
        widget.setPalette(palette)


class MetadataPanel(QtWidgets.QWidget):
    """The widget that effectively is the GUI to edit metadata."""

    def __init__(self, file_reader: PyPDF2.PdfReader, file_path: str) -> None:
        """Create the widget from a PdfReader object."""
        super().__init__()
        self.file_path = file_path
        self.file_reader = file_reader
        self.backup = True
        self.tags = defaultdict(TagData)
        self.create_tags()
        self.form = QtWidgets.QFormLayout(self)
        self.other_interactive_widgets = {}
        self.build_form()

    def create_tags(self) -> None:
        """Create all objects related to each tag."""
        for tag in TAGS:
            self.tags[tag] = TagData.from_metadata_interactive(
                self.file_reader.metadata.get(tag, "")
            )

        for tag, value in self.file_reader.metadata.items():
            if tag not in TAGS:
                self.tags[tag] = TagData.from_metadata_not_interactive(value)

    def build_form(self) -> None:
        """Create the form from the tags."""
        # File name
        title = QtWidgets.QLabel(Path(self.file_path).name)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setFont(QtGui.QFont("Sans Serif", 14))
        self.form.addRow(title)
        # Empty space
        self.form.addRow(QtWidgets.QLabel())
        # Path
        path_field = QtWidgets.QLineEdit(str(self.file_path))
        path_field.setEnabled(False)
        self.form.addRow("Path", path_field)
        # Editable fields
        for tag in TAGS:
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.addWidget(self.tags[tag].line_edit)
            row_layout.addWidget(self.tags[tag].reset_button)
            self.form.addRow(tag[1:], row_layout)
        # Other fields
        for tag, data in self.tags.items():
            if not data.interactive:
                self.form.addRow(tag[1:], data.line_edit)
        # Empty space
        self.form.addRow(QtWidgets.QLabel())
        # Save/Reset buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        save_button = QtWidgets.QPushButton("Save")
        reset_button = QtWidgets.QPushButton("Reset All")
        save_button.clicked.connect(self.save_file)
        for data in self.tags.values():
            reset_button.clicked.connect(data.reset_function)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(reset_button)
        self.other_interactive_widgets["save"] = save_button
        self.other_interactive_widgets["reset"] = reset_button
        self.form.addRow(buttons_layout)

    def save_file(self) -> None:
        """Save the file."""
        if all(not data.modified for data in self.tags.values()):
            return
        for data in self.tags.values():
            data.save_function()
        if self.backup:
            self.create_file_backup(self.file_path)
        file_writer = PyPDF2.PdfWriter()
        file_writer.clone_reader_document_root(self.file_reader)
        file_writer.add_metadata(
            {tag: data.value for tag, data in self.tags.items() if data.value}
        )
        with open(self.file_path, "wb") as f:
            file_writer.write(f)

    def create_file_backup(self, file_path: str) -> None:
        """Rename the file for backup purposes.

        If a file already exist with the backup name,
        keep trying with an increasing counter."""

        i = 0
        while True:
            try:
                os.rename(file_path, f"{file_path}.bak{i if i else ''}")
            except FileExistsError:
                i += 1
            except FileNotFoundError:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Missing file",
                    (
                        "The backup file was not created."
                        "<p>"
                        "The original file may have been renamed, moved, or deleted."
                    ),
                )
                return
            else:
                return


class MainWindow(QtWidgets.QMainWindow):
    """Instance of the actual GUI."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(APPLICATION_NAME)
        self.setGeometry(400, 400, 500, 500)
        self.actions = {}
        self.create_actions()
        self.create_menu()
        self.central_widget = QtWidgets.QWidget()
        self.setAcceptDrops(True)
        self.show()

    def create_actions(self) -> None:
        """Create the menu actions."""
        open_action = QtGui.QAction("Open")
        open_action.triggered.connect(self.select_file)
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        quit_action = QtGui.QAction("Quit")
        quit_action.triggered.connect(self.close)
        about_action = QtGui.QAction("About")
        about_action.triggered.connect(self.show_about)
        self.actions["open"] = open_action
        self.actions["quit"] = quit_action
        self.actions["about"] = about_action

    def create_menu(self) -> None:
        """Menu creation."""
        self.menuBar().setNativeMenuBar(False)
        file_menu = self.menuBar().addMenu("File")
        help_menu = self.menuBar().addMenu("Help")
        file_menu.addAction(self.actions["open"])
        file_menu.addAction(self.actions["quit"])
        help_menu.addAction(self.actions["about"])

    def show_about(self) -> None:
        """Display "About" information."""
        QtWidgets.QMessageBox.about(
            self,
            "About",
            f"""
            <p>PDF Metadata Editor v{__version__}</p>

            Source code available on <a href="{URL_GITHUB}">GitHub</a>
            """,
        )

    def display_metadata(self, file_path: str) -> None:
        """Create the GUI for the given file path, if possible."""
        if file_path:
            file_object = self.open_file(file_path)
            if file_object is not None:
                self.central_widget = MetadataPanel(file_object, file_path)
                self.setCentralWidget(self.central_widget)

    def select_file(self) -> None:
        """Handle file selection.

        Open a standard file selection window, with .pdf extension as default filter.
        If the user selects a file, set it as current file, and open it in the current session.
        """
        # getOpenFileName returns a tuple of strings (path, filter)
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select file",
            os.path.expanduser("~"),
            "PDF files (*.pdf);;All files (*.*)",
        )
        self.display_metadata(file_path)

    # Reimplement dragEnterEvent class method
    # pylint:disable-next=invalid-name
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Only accept drag events for certain data."""
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    # Reimplement dropEvent class method
    # pylint:disable-next=invalid-name
    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Attempt to open the file dropped onto the window."""
        for url in event.mimeData().urls():
            self.display_metadata(str(url.toLocalFile()))

    def open_file(self, file_path: str) -> PyPDF2.PdfReader:
        """Return the PdfReader object for the current file, if possible.

        If the file is password-protected, prompt the user to insert the password
        until either the correct password is provided or the 'cancel' button is pressed.
        Display an error message in case of incorrect password or if the file cannot be opened."""
        # Catch files that cannot be read (e.g. non-pdf files).
        try:
            file_reader = PyPDF2.PdfReader(file_path)
        except PdfReadError:
            QtWidgets.QMessageBox.critical(
                self, "Error", "The file could not be opened"
            )
            return None
        if file_reader.is_encrypted:
            decrypted = None
            while not decrypted:
                password, ok = QtWidgets.QInputDialog.getText(
                    self,
                    "Encrypted file",
                    "Insert password:",
                    QtWidgets.QLineEdit.EchoMode.Password,
                )
                # Do nothing if the Cancel button is selected.
                if not ok:
                    return None
                decrypted = file_reader.decrypt(password)
                # Display an error message if the password is incorrect.
                if not decrypted:
                    QtWidgets.QMessageBox.critical(self, "Error", "Incorrect password")
        # Robustness check, ask confirmation from the user to continue.
        try:
            file_reader_robust = PyPDF2.PdfReader(
                file_path,
                strict=True,
                password=password if file_reader.is_encrypted else None,
            )
            assert file_reader_robust.metadata
        except PdfReadError:
            answer = QtWidgets.QMessageBox.question(
                self,
                "Warning",
                (
                    "The selected file does not seem to follow PDF specifications."
                    "<br>"
                    "Attempting to alter the file may result in unexpected behaviour."
                    "<p>"
                    "Do you wish to continue?"
                ),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return None
        except AssertionError:
            pass

        return file_reader


def main() -> None:
    """Main loop."""
    app = QtWidgets.QApplication(sys.argv)
    # The window must be assigned to an object
    # pylint: disable-next=unused-variable
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
