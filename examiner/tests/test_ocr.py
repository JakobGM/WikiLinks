from os import environ

from pathlib import Path

from examiner.ocr import PdfReader

import pytest


pytestmark = pytest.mark.skipif(
    (
        'TRAVIS' in environ or
        environ['LC_ALL'] != 'C' or
        environ['PYTHONIOENCODING'] != 'UTF-8'
    ),
    reason='Travis does not support Tesseract 4.0 at this time.',
)


@pytest.fixture
def pdf_path() -> Path:
    """Return path to PDF that hos no text metadata and needs OCR."""
    return Path(__file__).parent / 'data' / 'ocr.pdf'


def test_creation_of_temporary_tiff_file(pdf_path):
    """PdfReader should create TIFF files in alphabetical order wrt. page num"""
    pdf_reader = PdfReader(path=pdf_path)
    tiff_directory = pdf_reader._tiff_directory()
    tiff_files = [tiff_file.name for tiff_file in tiff_directory.iterdir()]
    assert sorted(tiff_files) == ['0001.tif', '0002.tif']


def test_read_text(pdf_path):
    """You should be able to get OCRed text."""
    pdf_reader = PdfReader(path=pdf_path)
    text = pdf_reader.ocr_text()

    # We hard code this comparison to keep track of all changes to this metric
    assert pdf_reader.mean_confidence == 89

    # Check if we have two pages seperated by pagebreaks
    assert len(text.split('\f')) == 2

    # Content on the first page (important that this is at the beginning)
    assert 'Norwegian University of Science and Technology' in text[:50]

    # Content on second page (important that this is at the end)
    assert 'two requirements' in text[-50:]

    # The double-f in affine is hard for bad OCR algorithms
    assert 'affine' in text
