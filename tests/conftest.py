"""Fixtures."""

import shutil
from pathlib import Path
from typing import Generator

import pytest
from PyQt6 import QtWidgets

from pdfMetadataEditor import editor

TEST_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = TEST_ROOT.parent
SAMPLE_ROOT = PROJECT_ROOT / "samples"


@pytest.fixture
def not_pdf(tmp_path: Path) -> Generator[Path, None, None]:
    """Non-pdf file."""
    copy_path = shutil.copy2(SAMPLE_ROOT / "not-a-pdf.txt", tmp_path / "file.pdf")
    yield copy_path


@pytest.fixture
def base_pdf(tmp_path: Path) -> Generator[Path, None, None]:
    """Empty pdf file."""
    copy_path = shutil.copy2(
        SAMPLE_ROOT / "minimal-document.pdf", tmp_path / "file.pdf"
    )
    yield copy_path


@pytest.fixture
def encrypted_pdf_both(tmp_path: Path) -> Generator[Path, None, None]:
    """Pdf file encrypted with both owner and user password.

    Owner password: foo
    User password: bar"""
    copy_path = shutil.copy2(
        SAMPLE_ROOT / "r6-both-passwords.pdf", tmp_path / "file.pdf"
    )
    yield copy_path


@pytest.fixture
def encrypted_pdf_user(tmp_path: Path) -> Generator[Path, None, None]:
    """Pdf file encrypted with a user password.

    User password: asdfzxcv"""
    copy_path = shutil.copy2(
        SAMPLE_ROOT / "r6-both-passwords.pdf", tmp_path / "file.pdf"
    )
    yield copy_path


@pytest.fixture
def window(
    qapp: QtWidgets.QApplication,  # pylint: disable=unused-argument
) -> Generator[editor.MainWindow, None, None]:
    """A new window of the application."""
    app_window = editor.MainWindow()
    yield app_window
