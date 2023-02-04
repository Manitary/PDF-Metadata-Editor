"""Tests."""

import os
from pytestqt import qtbot
from PyQt6 import QtWidgets
from pdfMetadataEditor import editor

PASSWORD = "asdfzxcv"
PASSWORD_BOTH = "foo"


def object_bytes(file_path: str) -> bytes:
    """Return the byte object obtained by reading a given file."""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return file_bytes


def test_open_unencrypted_pdf(new_window: editor.MainWindow, base_pdf: str) -> None:
    """Open a trivial pdf file."""
    new_window.file_path = base_pdf
    file_reader = new_window.open_file(new_window.file_path)
    assert file_reader.metadata
    # PdfReader metadata attribute is accessible if the document is not encrypted


def test_open_encrypted_pdf_correct_password(
    new_window: editor.MainWindow, encrypted_pdf_both: str, monkeypatch
) -> None:
    """Open an encrypted pdf file."""
    monkeypatch.setattr(
        QtWidgets.QInputDialog, "getText", lambda *args: (PASSWORD_BOTH, True)
    )
    new_window.file_path = encrypted_pdf_both
    file_reader = new_window.open_file(new_window.file_path)
    assert file_reader.metadata
    # PdfReader metadata attribute is accessible if the document is successfully decrypted.


def test_dont_open_encrypted_pdf(
    new_window: editor.MainWindow, encrypted_pdf_both: str, monkeypatch
) -> None:
    """Fail to open an encrypted pdf file by not submitting a password."""
    monkeypatch.setattr(QtWidgets.QInputDialog, "getText", lambda *args: ("", False))
    new_window.file_path = encrypted_pdf_both
    file_reader = new_window.open_file(new_window.file_path)
    assert file_reader is None


def test_save_file_no_actions(new_window: editor.MainWindow, base_pdf: str) -> None:
    """Don't do anything when opening and saving a file."""
    expected = object_bytes(base_pdf)
    new_window.display_metadata(base_pdf)
    new_window.central_widget.save_file()
    files = os.listdir(os.path.dirname(base_pdf))
    file_bytes = object_bytes(base_pdf)
    assert len(files) == 1
    assert expected == file_bytes


def test_save_file_after_edit_reset(
    qtbot, new_window: editor.MainWindow, base_pdf: str
) -> None:
    """Test what happens when a field is edited and then reset."""
    expected = object_bytes(base_pdf)
    new_window.display_metadata(base_pdf)
    qtbot.keyPress(new_window.central_widget.tags["/Title"].line_edit, "a")
    new_window.central_widget.other_interactive_widgets["reset"].click()
    new_window.central_widget.save_file()
    files = os.listdir(os.path.dirname(base_pdf))
    file_bytes = object_bytes(base_pdf)
    assert len(files) == 1
    assert expected == file_bytes


def test_save_file_after_field_edit(
    qtbot,
    new_window: editor.MainWindow,
    base_pdf: str,
) -> None:
    """Test what happens when a metadata is edited and changes are saved.

    * A new file is created.
    * The bytes of the backup file are identical to those of the original file.
    * The bytes of the new file are different from those of the original file."""
    old_bytes = object_bytes(base_pdf)
    new_window.display_metadata(base_pdf)
    qtbot.keyPress(new_window.central_widget.tags["/Title"].line_edit, "a")
    new_window.central_widget.save_file()
    files = os.listdir(os.path.dirname(base_pdf))
    assert len(files) == 2
    assert old_bytes == object_bytes(os.path.dirname(base_pdf) + "/file.pdf.bak")
    assert old_bytes != object_bytes(os.path.dirname(base_pdf) + "/file.pdf")
