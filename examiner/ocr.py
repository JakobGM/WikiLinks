import logging
from os import environ

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union


logger = logging.getLogger()


if environ['LC_ALL'] != 'C' or environ['PYTHONIOENCODING'] != 'UTF-8':
    logger.critical(
        'PDF OCR disabled! You need to set environment variables: '
        'export LC_ALL=C && export PYTHONIOENCODING=UTF-8'
    )
else:
    try:
        from tesserocr import PyTessBaseAPI
        from wand.image import Color, Image
    except ImportError:
        logger.critical(
            'Tesserocr and/or Wand is not properly installed! '
            'PdfReader.ocr_text() will raise on invocation!',
        )


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
        text = []
        tiff_files = sorted(tiff_directory.iterdir())
        with PyTessBaseAPI(lang='nor+eng+equ', path=str(TESSDATA_DIR)) as api:
            for page in tiff_files:
                api.SetImageFile(str(page))
                text.append(api.GetUTF8Text())

        return '\f'.join(text)

    def _tiff_directory(self) -> Path:
        """
        Return Path object to directory TIFF files.

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
        with Image(filename=str(self.path), resolution=300) as image:
            for num, page in enumerate(image.sequence):
                page = Image(page)
                page.format = 'tif'
                page.compression_quality = 100
                page.background_color = Color(string='white')
                page.save(filename=f'{self._tmp_tiff_directory.name}/{num}.tif')

        return Path(self._tmp_tiff_directory.name)
