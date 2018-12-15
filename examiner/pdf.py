import logging
import subprocess

from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Union

import pdftotext


OCR_ENABLED = True
logger = logging.getLogger()


if environ['LC_ALL'] != 'C' or environ['PYTHONIOENCODING'] != 'UTF-8':
    logger.critical(
        'PDF OCR disabled! You need to set environment variables: '
        'export LC_ALL=C && export PYTHONIOENCODING=UTF-8'
    )
    OCR_ENABLED = False
else:
    try:
        from tesserocr import PyTessBaseAPI
    except ImportError:
        logger.critical(
            'Tesserocr is not properly installed! OCR disabled.'
        )
        OCR_ENABLED = False


TESSDATA_DIR = Path(__file__).parent / 'tessdata'


class PdfReader:
    def __init__(self, path: Union[Path, str]) -> None:
        """
        Construct PdfReader object.

        :param path: Absolute path to PDF document.
        """
        self.path = Path(path)
        if not self.path.is_absolute():
            raise ValueError(f'PdfReader initialized with relative path {path}')

    def read_text(self, *, allow_ocr: bool) -> Optional[str]:
        """
        Return text content of PDF.

        :param allow_ocr: If text cant be extracted from PDF directly, since
          it does not contain text metadata, text will be extracted by OCR if
          True. This is much slower, approximately ~5s per page.
        :return: String of PDF text content, pages seperated with pagebreaks.
        """
        with open(self.path, 'rb') as file:
            pdf = pdftotext.PDF(file)
        text = '\f'.join(pdf)

        if len(text) > 1:
            return text
        elif allow_ocr and OCR_ENABLED:
            return self.ocr_text()
        else:
            return None

    def ocr_text(self) -> str:
        """
        Return text contained in PDF document.

        Uses Tesseract for OCR. May be quite slow; ~5 seconds per page.

        Uses Norwegian, English, and math equations training data set for
        conversion.

        :return: UTF-8 encoded string representing the content of the documemt.
          Page breaks are inserted between each page, i.e. \f
        """
        tiff_directory = self._tiff_directory()
        self.confidences = []
        text = []
        tiff_files = sorted(tiff_directory.iterdir())
        with PyTessBaseAPI(lang='nor+eng+equ', path=str(TESSDATA_DIR)) as api:
            for page in tiff_files:
                api.SetImageFile(str(page))
                text.append(api.GetUTF8Text())
                self.confidences.extend(api.AllWordConfidences())

        self.mean_confidence = int(
            sum(self.confidences) / len(self.confidences),
        )
        return '\f'.join(text)

    def _tiff_directory(self) -> Path:
        """
        Return Path object to directory containing TIFF files.

        One TIFF image is created for each page in the PDF, and are sorted in
        alphabetical order wrt. page number of the original PDF. This is so
        because tesserocr does not support multi-page TIFFs at the date of this
        implementation.

        NB! The TIFF files are contained in a tempfile.TemporaryDirectory, and
        all files are deleted when this object goes out of scope.
        """
        if hasattr(self, '_tmp_tiff_directory'):
            return Path(self._tmp_tiff_directory.name)

        self._tmp_tiff_directory = TemporaryDirectory()

        # For choice of parameters, see:
        # https://mazira.com/blog/optimal-image-conversion-settings-tesseract-ocr
        subprocess.run([
            # Using GhostScript for PDF -> TIFF conversion
            'gs',
            # Prevent non-neccessary output
            '-q',
            '-dQUIET',
            # Disable prompt and pause after each page
            '-dNOPAUSE',
            # Convert to TIFF with 16-bit colors
            # https://ghostscript.com/doc/9.21/Devices.htm#TIFF
            '-sDEVICE=tiff48nc',
            # Split into one TIFF file for each page in the PDF
            f'-sOutputFile={self._tmp_tiff_directory.name}/%04d.tif',
            # Use 300 DPI
            '-r300',
            # Interpolate upscaled documents
            '-dINTERPOLATE',
            # Use 8 threads for faster performance
            '-dNumRenderingThreads=8',
            # Prevent unwanted file writing
            '-dSAFER',
            # PDF to convert
            str(self.path),
            # The following block contains postcript code
            '-c',
            # Allocate 30MB extra memory for speed increase
            '30000000',
            'setvmthreshold',
            # Quit the ghostscript prompt when done
            'quit',
            '-f',
        ])
        return Path(self._tmp_tiff_directory.name)
