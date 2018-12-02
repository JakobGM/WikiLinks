from collections import namedtuple

import pytest

from examiner.parsers import ExamURLParser, Language, Season


class ExamURL:
    def __init__(
        self,
        url: str,
        code: str,
        year: int,
        season: Season,
        solutions: bool,
        language: Language,
    ):
        self.url = url
        self.code = code
        self.year = year
        self.season = season
        self.solutions = solutions
        self.language = language

    def __repr__(self) -> str:
        return f'ExamURL(url={self.url}'


ExamURLs = (
    ExamURL(
        url='http://www.math.ntnu.no/emner/TMA4130/2013h/oldExams/eksamen-bok_2006v.pdf',
        code='TMA4130',
        year=2006,
        season=Season.SPRING,
        solutions=False,
        language=Language.BOKMAL,
    ),
    ExamURL(
        url='http://www.math.ntnu.no/emner/TMA4130/2013h/oldExams/lf-en_2006v.pdf',
        code='TMA4130',
        year=2006,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
    ),
    ExamURL(
        url='https://wiki.math.ntnu.no/_media/tma4130/2017h/kont_bok.pdf',
        code='TMA4130',
        year=2017,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.BOKMAL,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=42405f&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2FTMA4115_v18_kont_nn.pdf',
        code='TMA4115',
        year=2018,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.NYNORSK,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=113012&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4115v16_english_solutions.pdf',
        code='TMA4115',
        year=2016,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=113012&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4115v16_english_solutions.pdf',
        code='TMA4115',
        year=2016,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=99296a&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4110des11.pdf',
        code='TMA4110',
        year=2011,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.UNKNOWN,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/emner/TMA4130/2013h/oldExams/eksamen-bok_2006.pdf',
        code='TMA4130',
        year=2006,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=88d701&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Fscanned_from_a_xerox_multifunction_device001_25_.pdf',
        code='TMA4110',
        year=None,
        season=Season.UNKNOWN,
        solutions=False,
        language=Language.UNKNOWN,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=7df847&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4115juni08.pdf',
        code='TMA4115',
        year=2008,
        season=Season.SPRING,
        solutions=False,
        language=Language.NORWEGIAN,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=61b866&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2F2007may.pdf',
        code='TMA4110',
        year=2007,
        season=Season.SPRING,
        solutions=False,
        language=Language.ENGLISH,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4100/eksamen/sif5003_2002-07-30.pdf',
        code='TMA4100',
        year=2002,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.UNKNOWN,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4100/eksamen/sif5003_1999-12-08_lf.pdf',
        code='TMA4100',
        year=1999,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.NORWEGIAN,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4105/eksamen/sif5005_00k.pdf',
        code='TMA4105',
        year=2000,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.NORWEGIAN,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4180/2015v/lf_summer15.pdf',
        code='TMA4180',
        year=2015,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4305/exam/tma4305_2017-11_sol.pdf',
        code='TMA4305',
        year=2017,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.ENGLISH,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=7bbce9&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4140%2F2009h%2Feksamener%2Fh2012-lf.pdf',
        code='TMA4140',
        year=2012,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.NORWEGIAN,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4130/2016h/loesningsforslag_tma4130_h15_v2.pdf',
        code='TMA4130',
        year=2015,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.NORWEGIAN,
    ),
)

class TestExamURLParser:
    @pytest.mark.parametrize('exam', ExamURLs)
    def test_getting_url(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.url == exam.url

    @pytest.mark.parametrize('exam', ExamURLs)
    def test_year_parsing(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.year == exam.year

    @pytest.mark.parametrize('exam', ExamURLs)
    def test_course_code_parsing(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.code == exam.code

    @pytest.mark.parametrize('exam', ExamURLs)
    def test_season_parser(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.season == exam.season

    @pytest.mark.parametrize('exam', ExamURLs)
    def test_solutions_parser(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.solutions == exam.solutions

    @pytest.mark.xfail(strict=True)
    @pytest.mark.parametrize('exam', ExamURLs)
    def test_language_parser(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.language == exam.language
