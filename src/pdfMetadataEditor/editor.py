"""New version"""

import sys
import PyPDF2
from PyQt6 import QtWidgets  # , QtGui, QtCore
from PyPDF2.errors import FileNotDecryptedError  # , WrongPasswordError

# import os
# from pathlib import Path


def show_exception(parent: QtWidgets.QWidget, exception) -> None:
    """Display an error message when an exception occurs."""
    QtWidgets.QMessageBox.critical(
        parent=parent,
        title="Error",
        text=f"""An exception of type {type(exception).__name__} occurred.
<p>Arguments:\n{exception.args!r}""",
    )


class MainWindow(QtWidgets.QMainWindow):
    """Instance of the actual GUI."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # self.initialiseUI()

    def open_file(self, file_path: str) -> PyPDF2.PdfReader:
        """Return the PdfReader object for the given path, if possible."""
        try:
            file_reader = PyPDF2.PdfReader(file_path)
            return file_reader
        except FileNotDecryptedError:
            return None  # TODO: handle file description


def main() -> None:
    """Main loop."""
    app = QtWidgets.QApplication(sys.argv)
    MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
