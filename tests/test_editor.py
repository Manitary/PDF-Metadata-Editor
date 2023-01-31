"""Tests."""

# import os
# from pdfMetadataEditor import editor


def test_open_unencrypted_pdf(new_window, base_pdf) -> None:
    """Open a trivial pdf file."""
    assert new_window.open_file(base_pdf) is not None
