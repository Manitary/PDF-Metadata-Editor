from typing import Generator
from pathlib import Path
import pytest


TEST_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = TEST_ROOT.parent
SAMPLE_ROOT = PROJECT_ROOT / "samples"


@pytest.fixture
def empty_pdf() -> Generator[Path, None, None]:
    """Empty pdf file."""
    yield SAMPLE_ROOT / "minimal-document.pdf"
