"""Tests."""

import os
from pathlib import Path
import PyPDF2
import pytest
from pytestqt.qtbot import QtBot
from PyQt6 import QtWidgets
from pdfMetadataEditor import editor

PASSWORD = "asdfzxcv"
PASSWORD_BOTH = "foo"


def test_open_unencrypted_pdf(window: editor.MainWindow, base_pdf: Path) -> None:
    """Open a trivial pdf file."""
    window.file_path = base_pdf
    file_reader = window.open_file(window.file_path)
    assert file_reader.metadata
    # PdfReader metadata attribute is accessible if the document is not encrypted


def test_open_encrypted_pdf_correct_password(
    window: editor.MainWindow, encrypted_pdf_both: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Open an encrypted pdf file."""
    monkeypatch.setattr(
        QtWidgets.QInputDialog, "getText", lambda *args: (PASSWORD_BOTH, True)
    )
    window.file_path = encrypted_pdf_both
    file_reader = window.open_file(window.file_path)
    assert file_reader.metadata
    # PdfReader metadata attribute is accessible if the document is successfully decrypted.


def test_dont_open_encrypted_pdf(
    window: editor.MainWindow, encrypted_pdf_both: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fail to open an encrypted pdf file by not submitting a password."""
    monkeypatch.setattr(QtWidgets.QInputDialog, "getText", lambda *args: ("", False))
    window.file_path = encrypted_pdf_both
    file_reader = window.open_file(window.file_path)
    assert file_reader is None


def test_save_file_no_actions(window: editor.MainWindow, base_pdf: Path) -> None:
    """Don't do anything when opening and saving a file."""
    expected = base_pdf.read_bytes()
    file_name = base_pdf.name
    dir_path = base_pdf.parent
    window.display_metadata(base_pdf)
    window.central_widget.save_file()
    files = os.listdir(dir_path)
    # No new file is created
    assert len(files) == 1
    # The file is not renamed
    assert files[0] == file_name
    # The contents of the file have not changed
    assert (dir_path / file_name).read_bytes() == expected


@pytest.mark.parametrize("tag", editor.TAGS)
def test_save_file_after_one_edit_reset(
    qtbot: QtBot, window: editor.MainWindow, base_pdf: Path, tag: str
) -> None:
    """A metadata field is edited and then reset.

    Parameter: the tag that is edited."""
    expected = base_pdf.read_bytes()
    file_name = base_pdf.name
    dir_path = base_pdf.parent
    window.display_metadata(base_pdf)
    qtbot.keyPress(window.central_widget.tags[tag].line_edit, "a")
    window.central_widget.tags[tag].reset_button.click()
    window.central_widget.save_file()
    files = os.listdir(dir_path)
    # No new file is created
    assert len(files) == 1
    # The file is not renamed
    assert files[0] == file_name
    # The contents of the file have not changed
    assert (dir_path / file_name).read_bytes() == expected


def test_save_file_after_all_edit_reset(
    qtbot: QtBot, window: editor.MainWindow, base_pdf: Path
) -> None:
    """All metadata fields are edited and reset using the Reset All button."""
    expected = base_pdf.read_bytes()
    file_name = base_pdf.name
    dir_path = base_pdf.parent
    window.display_metadata(base_pdf)
    for tag in editor.TAGS:
        qtbot.keyPress(window.central_widget.tags[tag].line_edit, "a")
    window.central_widget.other_interactive_widgets["reset"].click()
    window.central_widget.save_file()
    files = os.listdir(dir_path)
    # No new file is created
    assert len(files) == 1
    # The file is not renamed
    assert files[0] == file_name
    # The contents of the file have not changed
    assert (dir_path / file_name).read_bytes() == expected


@pytest.mark.parametrize("tag", editor.TAGS)
def test_save_file_after_field_edit(
    qtbot: QtBot, window: editor.MainWindow, base_pdf: Path, tag: str
) -> None:
    """A metadata field is edited and changes are saved.

    * A new file is created.
    * The bytes of the backup file are identical to those of the original file.
    * The bytes of the new file are different from those of the original file."""
    original_bytes = base_pdf.read_bytes()
    file_name = base_pdf.name
    backup_name = file_name + ".bak"
    dir_path = base_pdf.parent
    original_reader = PyPDF2.PdfReader(base_pdf)
    window.display_metadata(base_pdf)
    qtbot.keyPress(window.central_widget.tags[tag].line_edit, "a")
    window.central_widget.save_file()
    new_reader = PyPDF2.PdfReader(dir_path / file_name)
    files = os.listdir(dir_path)
    # One new file is created
    assert len(files) == 2
    # The two files have the original and backup name
    assert files == [file_name, backup_name]
    # The backup file has the same contents as the original file
    assert (dir_path / backup_name).read_bytes() == original_bytes
    # The new file contents are different
    assert (dir_path / file_name).read_bytes() != original_bytes
    # All metadata except the modified one are the same
    assert all(
        value == new_reader.metadata[key]
        for key, value in original_reader.metadata.items()
        if key != tag
    )
    # The metadata field was edited correctly
    assert new_reader.metadata[tag] == original_reader.metadata.get(tag, "") + "a"
