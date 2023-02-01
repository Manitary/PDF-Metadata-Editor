"""Fixtures."""

from typing import Generator
from pathlib import Path
import shutil
import pytest
from pytestqt import qtbot
from pdfMetadataEditor import editor

TEST_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = TEST_ROOT.parent
SAMPLE_ROOT = PROJECT_ROOT / "samples"


@pytest.fixture
def base_pdf(tmp_path) -> Generator[Path, None, None]:
    """Empty pdf file."""
    copy_path = shutil.copy2(
        SAMPLE_ROOT / "minimal-document.pdf", tmp_path / "file.pdf"
    )
    yield copy_path


@pytest.fixture
def encrypted_pdf_both(tmp_path) -> Generator[Path, None, None]:
    """Pdf file encrypted with both owner and user password.

    Owner password: foo
    User password: bar"""
    copy_path = shutil.copy2(
        SAMPLE_ROOT / "r6-both-passwords.pdf", tmp_path / "file.pdf"
    )
    yield copy_path


@pytest.fixture
def encrypted_pdf_user(tmp_path) -> Generator[Path, None, None]:
    """Pdf file encrypted with a user password.

    User password: asdfzxcv"""
    copy_path = shutil.copy2(
        SAMPLE_ROOT / "r6-both-passwords.pdf", tmp_path / "file.pdf"
    )
    yield copy_path


@pytest.fixture
def new_window(qtbot) -> editor.MainWindow:
    """A new window of the application."""
    window = editor.MainWindow()
    yield window
