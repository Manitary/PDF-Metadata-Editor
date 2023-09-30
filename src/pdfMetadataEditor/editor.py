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


import os
import sys
from pathlib import Path
from typing import Any

import pypdf
from pypdf.errors import PdfReadError
from PyQt6 import QtCore, QtGui, QtWidgets

from ._version import __version__

APPLICATION_NAME = "PDF Metadata Editor"
URL_GITHUB = "https://github.com/Manitary/PDF-Metadata-Editor"

TAGS = ["/Title", "/Author", "/Subject", "/Keywords", "/Producer", "/Creator"]

BG_DEFAULT = QtCore.Qt.GlobalColor.white
BG_HIGHLIGHT = QtCore.Qt.GlobalColor.red


class TagData:
    """A class that handles the objects associated to a metadata tag.

    Attributes
    ----------
    value : str
        The metadata value.
    line_edit : QLineEdit
        The widget to display the value.
    """

    def __init__(self, value: str) -> None:
        self.value = value
        self.line_edit = QtWidgets.QLineEdit(str(value))  # ? Why str conversion


class TagDataNotInteractive(TagData):
    """A TagData object where the QLineEdit widget is non-interactive.

    Attributes
    ----------
    value : str
        The metadata value.
    line_edit : QLineEdit
        The widget to display the value.
    """

    def __init__(self, value: str) -> None:
        super().__init__(value)
        self.line_edit.setEnabled(False)


class TagDataInteractive(TagData):
    """An interactive TagData object.

    Attributes
    ----------
    value : ``str``
        The metadata value.
    line_edit : ``QLineEdit``
        The widget to display and modify the value.
    reset_button : ``QPushButton``
        The button to reset the QLineEdit text.
    reset_function : ``Callable[[], None]``
        The slot called when ``reset_button`` is pressed.
    modified : ``bool``
        True if the ``line_edit`` text differs from ``value``.

    Methods
    -------
    save_changes : ``Callable[[], None]``
        Save the ``line_edit`` text as new ``value``.
    """

    def __init__(self, value: str) -> None:
        super().__init__(value)
        self.line_edit.setEnabled(True)
        self.modified = False

        def reset_function() -> None:
            """Reset the text of ``line_edit`` to ``value``.

            It is the slot called when reset_button is pressed."""
            self.line_edit.setText(self.value)

        self.reset_function = reset_function
        self.reset_button = QtWidgets.QPushButton("Reset")
        self.reset_button.clicked.connect(reset_function)

        def edit_function() -> None:
            """Update ``modified`` and ``line_edit`` background colour based on its text.

            It is the slot called when ``line_edit`` text is changed."""
            if self.line_edit.text() == value:
                self.modified = False
                change_widget_background_colour(self.line_edit, BG_DEFAULT)
            else:
                self.modified = True
                change_widget_background_colour(self.line_edit, BG_HIGHLIGHT)

        self.line_edit.textChanged.connect(edit_function)

    def save_changes(self) -> None:
        """Set ``value`` to the text of ``line_edit``.

        Additionally, set ``modified`` to False, and reset ``line_edit`` background colour.
        It is called when the "Save" button is pressed."""
        self.modified = False
        self.value = self.line_edit.text()
        change_widget_background_colour(self.line_edit, BG_DEFAULT)


def change_widget_background_colour(
    widget: QtWidgets.QWidget, colour: QtCore.Qt.GlobalColor
) -> None:
    """Change a widget background colour to the assigned colour.

    Accept only PyQt pre-set colours.

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


def create_tags_from(
    file_reader: pypdf.PdfReader,
) -> tuple[dict[str, TagDataInteractive], dict[str, TagDataNotInteractive]]:
    """Return two tag -> TagData dictionaries based on the file_reader metadata
    (interactive, non-interactive)

    Parameters
    ----------
    file_reader : PdfReader
        The PdfReader object whose metadata are used.
    """
    assert file_reader.metadata
    metadata: dict[str, str] = dict(file_reader.metadata)
    tags_interactive = {tag: TagDataInteractive(metadata.get(tag, "")) for tag in TAGS}
    tags_not_interactive = {
        tag: TagDataNotInteractive(value)
        for tag, value in metadata.items()
        if tag not in TAGS
    }
    return tags_interactive, tags_not_interactive


class MetadataPanel(QtWidgets.QWidget):
    """A class that handles the effective GUI responsible for editing metadata.

    Attributes
    ----------
    file_path : str
        The path of the file whose metadata is going to be edited.
    file_reader : PdfReader
        The PdfReader object of the file at ``file_path``.
    form : QFormLayout
        The widget containing the interface used to edit metadata.
        (editable fields, Save/Reset buttons, etc.)
    tags : dict[str, TagData]
        A dictionary tag -> TagData for each metadata tag of the ``file_reader`` object.
        Allows easy access to the metadata values and the associated widgets contained in ``form``.
    other_interactive_widgets : dict[str, QtWidgets]
        A dictionary to easily access other interactive widgets that are not tied to a single tag.
    backup : bool
        If True, the file at ``file_path`` is renamed for backup before saving the edited metadata.

    Methods
    -------
    build_form()
        Create the widgets to include in ``form`` based on the contents of ``tags``.
    create_tags(file_reader)
        Return a dictionary tag -> TagData from the metadata of the file_reader object.
    create_file_backup()
        Rename the file at ``file_path`` for backup purposes.
    save_file()
        If any metadata field was edited, save the changes into a new file with path ``file_path``.
    """

    def __init__(self, file_reader: pypdf.PdfReader, file_path: str) -> None:
        """Create the widget from a PdfReader object.

        Parameters
        ----------
        file_reader : PdfReader
            The PdfReader object of the file whose metadata will be edited.
        file_path : str
            The path of the file used in ``file_reader``.
        """
        super().__init__()
        self.file_path = file_path
        self.file_reader = file_reader
        self.backup = True
        self.tags_interactive, self.tags_not_interactive = create_tags_from(file_reader)
        self.form, self.other_interactive_widgets = self.build_form()

    @property
    def tags(self) -> dict[str, TagDataInteractive | TagDataNotInteractive]:
        """Return all tags."""
        return self.tags_interactive | self.tags_not_interactive

    def build_form(
        self,
    ) -> tuple[QtWidgets.QFormLayout, dict[str, QtWidgets.QPushButton]]:
        """Return the form created from the tags, and the Save/Reset All buttons."""
        form = QtWidgets.QFormLayout(self)
        # File name
        title = QtWidgets.QLabel(Path(self.file_path).name)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setFont(QtGui.QFont("Sans Serif", 14))
        form.addRow(title)
        # Empty space
        form.addRow(QtWidgets.QLabel())
        # File Path
        path_field = QtWidgets.QLineEdit(str(self.file_path))
        path_field.setEnabled(False)
        form.addRow("Path", path_field)
        # Editable fields
        for tag, widget in self.tags_interactive.items():
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.addWidget(widget.line_edit)
            row_layout.addWidget(widget.reset_button)
            form.addRow(tag[1:], row_layout)
        # Other (non-editable) fields
        for tag, widget in self.tags_not_interactive.items():
            form.addRow(tag[1:], widget.line_edit)
        # Empty space
        form.addRow(QtWidgets.QLabel())
        # Save button
        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_file)
        # Reset All button
        reset_button = QtWidgets.QPushButton("Reset All")
        for data in self.tags_interactive.values():
            reset_button.clicked.connect(data.reset_function)
        # Align save/reset button horizontally
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(reset_button)
        form.addRow(buttons_layout)
        # Return the form and the save/reset buttons
        other_interactive_widgets = {"save": save_button, "reset": reset_button}
        return form, other_interactive_widgets

    def save_file(self) -> None:
        """If there was any change in metadata, save the changes.

        This is the slot connected to the Save button.
        The resulting file path is the ``file_path`` attribute.
        If the ``backup`` attribute is set to True, the existing file at ``file_path`` (if any)
        is renamed to back it up."""
        if all(not data.modified for data in self.tags_interactive.values()):
            return
        for data in self.tags_interactive.values():
            data.save_changes()
        if self.backup:
            self.create_file_backup(self.file_path)
        # Note: PdfWriter initialises the "/Producer" metadata with "pypdf".
        file_writer = pypdf.PdfWriter()
        file_writer.clone_reader_document_root(self.file_reader)
        file_writer.add_metadata(
            {tag: data.value for tag, data in self.tags.items() if data.value}
        )
        with open(self.file_path, "wb") as f:
            file_writer.write(f)

    def create_file_backup(self, file_path: str) -> None:
        """Rename the file for backup purposes.

        The file is renamed by adding a .bak extension.
        If such file already exists, it is renamed by appending .bak1,
        .bak2, and so on, until an available file name is found.
        If the file to rename does not exist, display a warning message.

        Parameters
        ----------
        file_path : str
            The path of the file to back up.
        """

        def new_file_name(i: int) -> str:
            return f"{file_path}.bak{i if i else ''}"

        i = 0
        # On Unix systems, os.rename does not raise exceptions if the destination already exists.
        while os.path.isfile(new_file_name(i)):
            i += 1
        try:
            os.rename(file_path, new_file_name(i))
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


class MainWindow(QtWidgets.QMainWindow):
    """A class that handles the instance of the actual GUI.

    Attributes
    ----------
    actions_dict : dict[str, QAction]
        A dictionary to easily access the actions used in the menu.
    central_widget : QWidget
        The interface to edit metadata.

    Methods
    -------
    create_actions()
        Return the actions to use in the menu.
    create_menu()
        Create the menu.
    show_about()
        Display the "About" information. It is connected to the "About" menu action.
    display_metadata(file_path)
        Create the interface to display and edit the metadata of the file at ``file_path``.
    select_file()
        Open the file selection window.
    dragEnterEvent()
        Handle dragging items on the main window.
        Reimplement the method inherited from QMainWindow.
    dropEvent()
        Handle dropping items on the main window.
        Reimplement the method inherited from QMainWindow.
    open_file(file_path)
        Return the PdfReader object of the file at ``file_path``, if possible.
        Include handling the decryption of password-protected files.
        Display an error message in case of failed decryption or if the file cannot be opened.
        Display a warning message if the file cannot be read in strict mode.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.setWindowTitle(APPLICATION_NAME)
        self.setGeometry(400, 400, 500, 500)
        self.actions_dict = self.create_actions()
        self.create_menu()
        self.central_widget = QtWidgets.QWidget()
        self.setAcceptDrops(True)
        self.show()

    def create_actions(self) -> dict[str, QtGui.QAction]:
        """Return a dictionary of menu actions.

        Actions
        -------
        open: open the file selection panel.
            Connected to the ``select_file`` method.
        close: close the program.
            Connected to the ``close`` method (inherited from QMainWindow).
        about: show the "About" message.
            Connected to the ``show_about`` method.
        """
        open_action = QtGui.QAction("Open")
        open_action.triggered.connect(self.select_file)
        open_action.setShortcut(QtGui.QKeySequence.StandardKey.Open)
        quit_action = QtGui.QAction("Quit")
        quit_action.triggered.connect(self.close)
        about_action = QtGui.QAction("About")
        about_action.triggered.connect(self.show_about)
        actions = {
            "open": open_action,
            "quit": quit_action,
            "about": about_action,
        }
        return actions

    def create_menu(self) -> None:
        """Create the menu.

        Menu
        ----
        File
            Open (ctrl-O)
            Quit
        Help
            About
        """
        self.menuBar().setNativeMenuBar(False)
        file_menu = self.menuBar().addMenu("File")
        help_menu = self.menuBar().addMenu("Help")
        file_menu.addAction(self.actions_dict["open"])
        file_menu.addAction(self.actions_dict["quit"])
        help_menu.addAction(self.actions_dict["about"])

    def show_about(self) -> None:
        """Display the "About" information."""
        QtWidgets.QMessageBox.about(
            self,
            "About",
            (
                f"{APPLICATION_NAME} v{__version__}"
                "<p>"
                f'Source code available on <a href="{URL_GITHUB}">GitHub</a>'
            ),
        )

    def display_metadata(self, file_path: str | Path) -> None:
        """Create the interface to edit metadata and attach it to the central widget of the window.

        Parameters
        ----------
        file_path : str
            The path of the file whose metadata will be displayed for editing.
        """
        if file_path:
            file_object = self.open_file(file_path)
            if file_object is not None:
                self.central_widget = MetadataPanel(file_object, str(file_path))
                self.setCentralWidget(self.central_widget)

    def select_file(self) -> None:
        """Handle file selection.

        Open a standard file selection window, with .pdf extension as default filter.
        If the user selects a file, open it in the current session.
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
    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent) -> None:
        """Only accept drag events for certain data.

        Parameters
        ----------
        event : QDragEnterEvent
        """
        # hasUrls is true when dragging files because of their path.
        if a0.mimeData().hasUrls():
            a0.accept()
        else:
            a0.ignore()

    # Reimplement dropEvent class method
    # pylint:disable-next=invalid-name
    def dropEvent(self, a0: QtGui.QDropEvent) -> None:
        """Attempt to open the file dropped onto the window."""
        for url in a0.mimeData().urls():
            self.display_metadata(url.toLocalFile())

    def open_file(self, file_path: str | Path) -> pypdf.PdfReader | None:
        """Return the PdfReader object for the file at ``file_path``, if possible.

        If the file cannot be opened (e.g. not a PDF file), display an error message.
        If the file is password-protected, prompt the user to insert the password
        until either the correct password is provided or the 'Cancel' button is pressed.
        Display an error message in case of incorrect password.
        If the file cannot be opened in strict mode, i.e. it does not follows 1.7 specifications,
        display a warning message asking the user whether to proceed.
        For more information about pypdf strict mode, see
        https://pypdf.readthedocs.io/en/latest/user/robustness.html.

        Parameters
        ----------
        file_path : str
            The file path to read.
        """
        # Catch files that cannot be read (e.g. non-pdf files).
        try:
            file_reader = pypdf.PdfReader(file_path)
        except PdfReadError:
            QtWidgets.QMessageBox.critical(
                self, "Error", "The file could not be opened"
            )
            return None
        # If the file is password-protected, prompt the user to insert the password.
        password = None
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
        # Robustness check. Ask confirmation from the user to continue.
        try:
            file_reader_robust = pypdf.PdfReader(
                file_path,
                strict=True,
                password=password if file_reader.is_encrypted else None,
            )
            assert file_reader_robust.metadata is not None
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
            # Do nothing unless the user chooses to proceed.
            if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                return None
        except AssertionError:
            pass

        return file_reader


def main() -> None:
    """The application main loop."""
    app = QtWidgets.QApplication(sys.argv)
    # The window must be assigned to an object
    # pylint: disable-next=unused-variable
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
