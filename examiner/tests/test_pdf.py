from os import environ

from pathlib import Path

from examiner.pdf import PdfReader

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


@pytest.fixture
def ocr_many_pages() -> Path:
    """PDF which requires OCR and has lots of pages."""
    return Path(__file__).parent / 'data' / 'ocr_many_pages.pdf'


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
    assert pdf_reader.page_confidences == [86, 91]

    # Check if we have two pages seperated by pagebreaks
    assert len(text.split('\f')) == 2

    # The same content can be extracted from the pages property
    assert '\f'.join(pdf_reader.pages) == text

    # Content on the first page (important that this is at the beginning)
    assert 'Norwegian University of Science and Technology' in text[:50]

    # Content on second page (important that this is at the end)
    assert 'two requirements' in text[-50:]

    # The double-f in affine is hard for bad OCR algorithms
    assert 'affine' in text


@pytest.mark.parametrize('allow_ocr', [True, False])
def test_read_text_of_text_indexed_pdf(allow_ocr, monkeypatch):
    """PdfReader should be able to read indexed pdf's quickly."""
    # This is a PDF which contains indexed text
    pdf_path = Path(__file__).parent / 'data' / 'matmod_exam_des_2017.pdf'

    # So the OCR method should never be called
    monkeypatch.delattr('examiner.pdf.PdfReader.ocr_text')

    # Now we read the indexed text
    pdf = PdfReader(path=pdf_path)
    text = pdf.read_text(allow_ocr=allow_ocr)

    # Ensure unicode string
    assert isinstance(text, str)

    # Check content
    assert 'Rottman' in text
    assert 'population model' in text
    assert 'this is not in the exam' not in text


def test_read_text_of_non_indexed_pdf_without_ocr(pdf_path):
    """Non-indexed PDFs should return None when OCR is not allowed."""
    pdf = PdfReader(path=pdf_path)
    assert pdf.read_text(allow_ocr=False) is None


def test_read_text_of_non_indexed_pdf_with_ocr(monkeypatch, pdf_path):
    """PdfReader should fall back to OCR if allowed for non indexed files."""
    monkeypatch.setattr(PdfReader, 'ocr_text', lambda self: 'content')
    pdf = PdfReader(path=pdf_path)
    assert pdf.read_text(allow_ocr=True) == 'content'


def test_pdf_with_many_pages_requires_ocr(ocr_many_pages):
    """PDF with many pages should still be detected as OCR-depending"""
    pdf = PdfReader(path=ocr_many_pages)
    assert pdf.read_text(allow_ocr=False) is None
