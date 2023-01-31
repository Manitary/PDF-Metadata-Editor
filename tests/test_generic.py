import os
import shutil
from PyPDF2 import PdfReader, PdfMerger


def test_trivial() -> None:
    assert True


def test_base_file(empty_pdf) -> None:
    file_reader = PdfReader(empty_pdf)
    assert os.path.isfile(empty_pdf)
    metadata = file_reader.metadata
    assert metadata["/Creator"] == "TeX"
    with open(empty_pdf, "rb+") as f:
        file_merger = PdfMerger()
        file_merger.append(f)
        file_merger.add_metadata({"/Author": "Test_Author", "/Title": "Test_Title"})
        file_merger.write(f)
    file_reader = PdfReader(empty_pdf)
    assert file_reader.metadata["/Author"] == "Test_Author"


def test_new_window(new_window) -> None:
    assert new_window
