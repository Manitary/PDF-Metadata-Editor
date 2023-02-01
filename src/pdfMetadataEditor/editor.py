"""New version"""

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
        # self.initialiseUI()

    def open_file(self, file_path: str, password: str = None) -> PyPDF2.PdfReader:
        """Return the PdfReader object for the given file, if possible.

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
    MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
