"""New version"""

import os
import sys
from pathlib import Path
from typing import Callable
import PyPDF2
from PyQt6 import QtWidgets, QtGui, QtCore
from PyPDF2.errors import PdfReadError

APPLICATION_NAME = "PDF Metadata Editor"
VERSION = 0.3
URL_GITHUB = "https://github.com/Manitary/PDF-Metadata-Editor"

TAGS = ["/Title", "/Author", "/Subject", "/Keywords", "/Producer", "/Creator"]


def show_exception(parent: QtWidgets.QWidget, exception) -> None:
    """Display an error message when an exception occurs."""
    QtWidgets.QMessageBox.critical(
        parent,
        "Error",
        f"""An exception of type {type(exception).__name__} occurred.
<p>Arguments:\n{exception.args!r}""",
    )


def create_file_backup(file_path: str) -> None:
    """Rename the file for backup purposes.

    If a file already exist with the backup name,
    keep trying with an increasing counter."""

    i = 0
    while True:
        try:
            os.rename(file_path, f"{file_path}.bak{i if i else ''}")
        except FileExistsError:
            i += 1
        else:
            break


def change_widget_background_colour(
    widget: QtWidgets.QWidget, colour: QtCore.Qt.GlobalColor
) -> None:
    """Change a widget background colour with the assigned colour.

    At the moment only works for PyQt pre-set colours."""
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
        self.metadata = file_reader.metadata.copy()
        self.backup = True
        self.modified_fields = set()
        self.form = QtWidgets.QFormLayout(self)
        self.build_form()

    def build_form(self) -> None:
        """Create the form from the metadata."""
        # File name
        title = QtWidgets.QLabel(Path(self.file_path).name)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setFont(QtGui.QFont("Sans Serif", 14))
        self.form.addRow(title)
        # Empty space
        self.form.addRow(QtWidgets.QLabel())
        # Editable fields
        # Create the Save/Reset All buttons here to connect signals
        save_button = QtWidgets.QPushButton("Save")
        reset_button = QtWidgets.QPushButton("Reset All")
        for tag in TAGS:
            field, reset_function, save_function = self.form_field_from_metadata(tag)
            reset_button.clicked.connect(reset_function)
            save_button.clicked.connect(save_function)
            self.form.addRow(tag[1:], field)
        # Other fields
        for tag, value in {
            (tag, value) for tag, value in self.metadata.items() if tag not in TAGS
        }:
            field = QtWidgets.QLineEdit(str(value))
            field.setEnabled(False)
            self.form.addRow(tag[1:], field)
        # Empty space
        self.form.addRow(QtWidgets.QLabel())
        # Save/Reset buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        save_button.clicked.connect(self.save_file)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(reset_button)
        self.form.addRow(buttons_layout)

    def form_field_from_metadata(
        self, tag: str
    ) -> tuple[QtWidgets.QHBoxLayout, Callable[[None], None]]:
        """Return the field for the form row and its reset button."""
        field = QtWidgets.QLineEdit(str(self.metadata.get(tag, "")))
        button = QtWidgets.QPushButton("Reset")

        def reset_function() -> None:
            field.setText(str(self.metadata.get(tag, "")))
            change_widget_background_colour(field, QtCore.Qt.GlobalColor.white)
            self.modified_fields.discard(tag)

        def save_field() -> None:
            self.metadata[tag] = field.text()
            change_widget_background_colour(field, QtCore.Qt.GlobalColor.white)

        def edit_function() -> None:
            change_widget_background_colour(field, QtCore.Qt.GlobalColor.red)
            self.modified_fields.add(tag)

        field.textEdited.connect(edit_function)
        button.clicked.connect(reset_function)
        row_layout = QtWidgets.QHBoxLayout()
        row_layout.addWidget(field)
        row_layout.addWidget(button)
        return row_layout, reset_function, save_field

    def save_file(self) -> None:
        """Save the file."""
        if not self.modified_fields:
            return
        if self.backup:
            create_file_backup(self.file_path)
        file_writer = PyPDF2.PdfWriter()
        file_writer.clone_reader_document_root(self.file_reader)
        file_writer.add_metadata(
            {tag: value for tag, value in self.metadata.items() if value}
        )
        with open(self.file_path, "wb") as f:
            file_writer.write(f)


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
            <p>PDF Metadata Editor v{VERSION}</p>

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
        try:
            file_reader = PyPDF2.PdfReader(file_path)
        except PdfReadError:
            QtWidgets.QMessageBox.critical(
                self, "Error", "The file could not be opened"
            )
        else:
            if not file_reader.is_encrypted:
                return file_reader
            while True:
                password, ok = QtWidgets.QInputDialog.getText(
                    self,
                    "Encrypted file",
                    "Insert password:",
                    QtWidgets.QLineEdit.EchoMode.Password,
                )
                if not ok:
                    return None
                decrypted = file_reader.decrypt(password)
                if decrypted:
                    return file_reader
                QtWidgets.QMessageBox.critical(self, "Error", "Incorrect password")
        return None


def main() -> None:
    """Main loop."""
    app = QtWidgets.QApplication(sys.argv)
    # The window must be assigned to an object
    # pylint: disable-next=unused-variable
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
