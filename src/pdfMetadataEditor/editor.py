"""New version"""

import os
import sys
import PyPDF2
from PyQt6 import QtWidgets  # , QtGui, QtCore
from PyPDF2.errors import PdfReadError

# import os
# from pathlib import Path


def show_exception(parent: QtWidgets.QWidget, exception) -> None:
    """Display an error message when an exception occurs."""
    QtWidgets.QMessageBox.critical(
        parent,
        "Error",
        f"""An exception of type {type(exception).__name__} occurred.
<p>Arguments:\n{exception.args!r}""",
    )


class MainWindow(QtWidgets.QMainWindow):
    """Instance of the actual GUI."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.file_path = None
        # self.initialiseUI()

    def select_file(self) -> None:
        """Handle file selection.

        Open a standard file selection window, with .pdf extension as default filter.
        If the user selects a file, set it as current file, and open it in the current session.
        """
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select file",
            os.path.expanduser("~"),
            "PDF files (*.pdf);;All files (*.*)",
        )  # getOpenFileName returns a tuple of strings (path, filter)
        if file_path:
            self.file_path = file_path
            self.open_file()

    def open_current_file(self) -> PyPDF2.PdfReader:
        """Return the PdfReader object for the current file, if possible.

        If the file is password-protected, prompt the user to insert the password
        until either the correct password is provided or the 'cancel' button is pressed.
        Display an error message in case of incorrect password or if the file cannot be opened."""
        try:
            file_reader = PyPDF2.PdfReader(self.file_path)
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
    MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
