import os
import shutil
from PyPDF2 import PdfReader, PdfMerger


def test_trivial() -> None:
    assert True


def test_base_file(tmp_path, empty_pdf) -> None:
    file_name = os.path.join(tmp_path, "file.pdf")
    shutil.copy2(empty_pdf, file_name)
    file_reader = PdfReader(file_name)
    assert os.path.isfile(file_name)
    metadata = file_reader.metadata
    assert metadata["/Creator"] == "TeX"
    with open(file_name, "rb+") as f:
        file_merger = PdfMerger()
        file_merger.append(f)
        file_merger.add_metadata({"/Author": "Test_Author", "/Title": "Test_Title"})
        file_merger.write(f)
    file_reader = PdfReader(file_name)
    assert file_reader.metadata["/Author"] == "Test_Author"
