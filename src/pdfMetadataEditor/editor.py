"""New version"""

from __future__ import annotations
import os
import sys
from pathlib import Path
import PyPDF2
from PyQt6 import QtWidgets, QtGui, QtCore
from PyPDF2.errors import PdfReadError


TAGS = ["/Title", "/Author", "/Subject", "/Keywords", "/Producer", "/Creator"]


def show_exception(parent: QtWidgets.QWidget, exception) -> None:
    """Display an error message when an exception occurs."""
    QtWidgets.QMessageBox.critical(
        parent,
        "Error",
        f"""An exception of type {type(exception).__name__} occurred.
<p>Arguments:\n{exception.args!r}""",
    )


def form_row_from_metadata(value: str) -> QtWidgets.QHBoxLayout:
    """Return the field for the form row and its reset button."""
    e = QtWidgets.QLineEdit(value)
    b = QtWidgets.QPushButton("Reset")
    b.clicked.connect(lambda: e.setText(value))
    h = QtWidgets.QHBoxLayout()
    h.addWidget(e)
    h.addWidget(b)
    return h, b


class MetadataPanel(QtWidgets.QWidget):
    """The widget that effectively is the GUI to edit metadata."""

    def __init__(self, file_object: PyPDF2.PdfReader, file_path: str) -> None:
        """Create the widget from a PdfReader object."""
        super().__init__()
        self.file_path = file_path
        self.file_object = file_object
        self.form = QtWidgets.QFormLayout(self)
        self.reset_buttons = []
        self.build_form(file_object.metadata)

    def build_form(self, metadata: dict) -> None:
        """Create the form from the metadata."""
        # File name
        title = QtWidgets.QLabel(Path(self.file_path).name)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setFont(QtGui.QFont("Sans Serif", 14))
        self.form.addRow(title)
        # Empty space
        self.form.addRow(QtWidgets.QLabel())
        # Editable fields
        for tag in TAGS:
            value = str(metadata.pop(tag, ""))
            field, button = form_row_from_metadata(value)
            self.reset_buttons.append(button)
            self.form.addRow(tag[1:], field)
        # Other fields
        for tag, value in metadata.items():
            field = QtWidgets.QLineEdit(str(value))
            field.setEnabled(False)
            self.form.addRow(tag[1:], field)
        # Empty space
        self.form.addRow(QtWidgets.QLabel())
        # Save/Reset buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_file)
        buttons_layout.addWidget(save_button)
        reset_button = QtWidgets.QPushButton("Reset All")
        reset_button.clicked.connect(self.reset_all)
        buttons_layout.addWidget(reset_button)
        self.form.addRow(buttons_layout)

    def reset_all(self) -> None:
        """Reset all fields."""
        for button in self.reset_buttons:
            button.click()

    def save_file(self) -> None:
        """Save the file."""


class MainWindow(QtWidgets.QMainWindow):
    """Instance of the actual GUI."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.create_menu()
        self.central_widget = QtWidgets.QWidget()
        # self.initialiseUI()
        self.show()

    def create_menu(self) -> None:
        """Menu creation (temporary)"""
        file_menu = self.menuBar().addMenu("File")
        self.open_action = QtGui.QAction("Open")
        self.open_action.triggered.connect(self.select_file)
        file_menu.addAction(self.open_action)

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


def main() -> None:
    """Main loop."""
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()  # the window must be assigned to an object
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
