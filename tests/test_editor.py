"""Tests."""

import os
from pathlib import Path
from unittest.mock import Mock
import PyPDF2
import pytest
from pytestqt.qtbot import QtBot
from PyQt6 import QtWidgets, QtCore
from pdfMetadataEditor import editor

PASSWORD = "asdfzxcv"
PASSWORD_BOTH = "foo"


def test_open_not_pdf(
    window: editor.MainWindow,
    not_pdf: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail to open a non-pdf file."""
    monkeypatch.setattr(
        QtWidgets.QMessageBox,
        "critical",
        lambda *args: None,
    )
    file_reader = window.open_file(not_pdf)
    assert file_reader is None


def test_open_unencrypted_pdf(window: editor.MainWindow, base_pdf: Path) -> None:
    """Open a trivial pdf file."""
    file_reader = window.open_file(base_pdf)
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


def test_open_encrypted_pdf_wrong_then_correct_password(
    window: editor.MainWindow, encrypted_pdf_both: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the wrong password and then the correct password to open an encrypted file."""
    mock = Mock(side_effect=[("wrong_password", True), (PASSWORD_BOTH, True)])
    monkeypatch.setattr(QtWidgets.QInputDialog, "getText", mock)
    monkeypatch.setattr(QtWidgets.QMessageBox, "critical", lambda *args: None)
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
    """A metadata field is edited and then reset using its reset button.

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


@pytest.mark.parametrize("tag", editor.TAGS)
def test_save_file_after_one_edit_reverted(
    qtbot: QtBot, window: editor.MainWindow, base_pdf: Path, tag: str
) -> None:
    """A metadata field is edited and then manually reverted.

    Parameter: the tag that is edited."""
    expected = base_pdf.read_bytes()
    file_name = base_pdf.name
    dir_path = base_pdf.parent
    window.display_metadata(base_pdf)
    qtbot.keyPress(window.central_widget.tags[tag].line_edit, "a")
    qtbot.keyPress(
        window.central_widget.tags[tag].line_edit, QtCore.Qt.Key.Key_Backspace
    )
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
    """A metadata field is edited and changes are saved."""
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
    # All metadata except the specified one are unchanged
    assert all(
        value == new_reader.metadata[key]
        for key, value in original_reader.metadata.items()
        if key != tag
    )
    # The specified metadata was edited correctly
    assert new_reader.metadata[tag] == original_reader.metadata.get(tag, "") + "a"


def test_modify_file_twice(
    qtbot: QtBot, window: editor.MainWindow, base_pdf: Path
) -> None:
    """The same file is modified and saved more than once.

    Test creation of backup files with overlapping names."""
    tag = "/Title"  # No need to parametrise this test
    original_bytes = base_pdf.read_bytes()
    file_name = base_pdf.name
    backup_name = file_name + ".bak"
    backup_name_1 = file_name + ".bak1"
    dir_path = base_pdf.parent
    window.display_metadata(base_pdf)
    qtbot.keyPress(window.central_widget.tags[tag].line_edit, "a")
    window.central_widget.save_file()
    qtbot.keyPress(window.central_widget.tags[tag].line_edit, "a")
    window.central_widget.save_file()
    files = os.listdir(dir_path)
    # Two new files are created
    assert len(files) == 3
    # The files have the correct names
    assert set(files) == {file_name, backup_name, backup_name_1}
    # The older backup file has the same contents as the original file
    assert (dir_path / backup_name).read_bytes() == original_bytes
    # Each file has the expected change in the given metadata field
    assert PyPDF2.PdfReader(dir_path / backup_name).metadata.get(
        tag, ""
    ) + "a" == PyPDF2.PdfReader(dir_path / backup_name_1).metadata.get(tag, "")
    assert (
        PyPDF2.PdfReader(dir_path / backup_name_1).metadata[tag] + "a"
        == PyPDF2.PdfReader(dir_path / file_name).metadata[tag]
    )
