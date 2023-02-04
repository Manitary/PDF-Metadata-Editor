"""Tests."""

from PyQt6 import QtWidgets
from pdfMetadataEditor import editor

PASSWORD = "asdfzxcv"
PASSWORD_BOTH = "foo"


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
