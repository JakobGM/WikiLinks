from typing import List, Optional

import pytest

from examiner.models import DocumentInfo
from examiner.parsers import ExamURLParser, Language, PdfParser, Season


class ExamURL:
    def __init__(
        self,
        url: str,
        code: str,
        year: int,
        season: Season,
        solutions: bool,
        language: Language,
        probably_exam: bool,
    ):
        self.url = url
        self.code = code
        self.year = year
        self.season = season
        self.solutions = solutions
        self.language = language
        self.probably_exam = probably_exam

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
        probably_exam=True,
    ),
    ExamURL(
        url='http://www.math.ntnu.no/emner/TMA4130/2013h/oldExams/lf-en_2006v.pdf',
        code='TMA4130',
        year=2006,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
        probably_exam=True,
    ),
    ExamURL(
        url='https://wiki.math.ntnu.no/_media/tma4130/2017h/kont_bok.pdf',
        code='TMA4130',
        year=2017,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=42405f&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2FTMA4115_v18_kont_nn.pdf',
        code='TMA4115',
        year=2018,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.NYNORSK,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=113012&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4115v16_english_solutions.pdf',
        code='TMA4115',
        year=2016,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=113012&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4115v16_english_solutions.pdf',
        code='TMA4115',
        year=2016,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=99296a&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4110des11.pdf',
        code='TMA4110',
        year=2011,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/emner/TMA4130/2013h/oldExams/eksamen-bok_2006.pdf',
        code='TMA4130',
        year=2006,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=88d701&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Fscanned_from_a_xerox_multifunction_device001_25_.pdf',
        code='TMA4110',
        year=None,
        season=Season.UNKNOWN,
        solutions=False,
        language=Language.UNKNOWN,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=7df847&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Ftma4115juni08.pdf',
        code='TMA4115',
        year=2008,
        season=Season.SPRING,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=61b866&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2F2007may.pdf',
        code='TMA4110',
        year=2007,
        season=Season.SPRING,
        solutions=False,
        language=Language.ENGLISH,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4100/eksamen/sif5003_2002-07-30.pdf',
        code='TMA4100',
        year=2002,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.UNKNOWN,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4100/eksamen/sif5003_1999-12-08_lf.pdf',
        code='TMA4100',
        year=1999,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4105/eksamen/sif5005_00k.pdf',
        code='TMA4105',
        year=2000,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.UNKNOWN,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4180/2015v/lf_summer15.pdf',
        code='TMA4180',
        year=2015,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
        probably_exam=False,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4305/exam/tma4305_2017-11_sol.pdf',
        code='TMA4305',
        year=2017,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.ENGLISH,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=7bbce9&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4140%2F2009h%2Feksamener%2Fh2012-lf.pdf',
        code='TMA4140',
        year=2012,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4130/2016h/loesningsforslag_tma4130_h15_v2.pdf',
        code='TMA4130',
        year=2015,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4130/2016h/oving2.pdf',
        code='TMA4130',
        year=2016,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.UNKNOWN,
        probably_exam=False,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=c5adfd&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2FTMA4115_v18_kont_no.pdf',
        code='TMA4115',
        year=2018,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=6d86b8&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2F2016hn.pdf',
        code='TMA4110',
        year=2016,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.UNKNOWN,  # TODO
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4140/2018h/midtsem_fasit18.pdf',
        code='TMA4140',
        year=2018,
        season=Season.AUTUMN,  # TODO
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=False,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/emner/TMA4240/eksamen/oppg/eksMai18n.pdf',
        code='TMA4240',
        year=2018,
        season=Season.SPRING,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/emner/TMA4240/eksamen/oppg/eksNov17n.pdf',
        code='TMA4240',
        year=2017,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/~davidlin/TMA4245-Statistikk/LFeksamener2006-2010.pdf',
        code='TMA4245',
        year=2006,
        season=Season.UNKNOWN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/emner/TMA4275/Eksamen/SolutionTMA4275-June2010-Probl2-3.pdf',
        code='TMA4275',
        year=2010,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/lib/exe/fetch.php?tok=9e4910&media=http%3A%2F%2Fwww.math.ntnu.no%2Femner%2FTMA4110%2Feksamen%2Fttm4115v15_ny.pdf',
        code='TTM4115',
        year=2015,
        season=Season.SPRING,
        solutions=False,
        language=Language.NYNORSK,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4105/eksamen/tma4105_12v_ny.pdf',
        code='TMA4105',
        year=2012,
        season=Season.SPRING,
        solutions=False,
        language=Language.NYNORSK,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4145/exams/tma4145eksh13bm.pdf',
        code='TMA4145',
        year=2013,
        season=Season.UNKNOWN,  # TODO
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4145/exams/tma4145eksh13nn.pdf',
        code='TMA4145',
        year=2013,
        season=Season.UNKNOWN,  # TODO
        solutions=False,
        language=Language.NYNORSK,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4105/eksamen/tma4105_13k.pdf',
        code='TMA4105',
        year=2013,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.UNKNOWN,
        probably_exam=True,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/emner/TMA4220/2012h/exam/eks_fem_2004_fasit.pdf',
        code='TMA4220',
        year=2004,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4190/2014v/loysforslag4190mai2014.pdf',
        code='TMA4190',
        year=2014,
        season=Season.SPRING,
        solutions=True,
        language=Language.NYNORSK,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://wiki.math.ntnu.no/_media/tma4320/2018v/tma_4320_physics_project_1.pdf',
        code='TMA4320',
        year=2018,
        season=Season.SPRING,
        solutions=False,
        language=Language.UNKNOWN,
        probably_exam=False,
    ),
    ExamURL(
        url=r'http://www.math.ntnu.no/~arvidn/TMA4295V09/TMA4295_2007_lf.pdf',
        code='TMA4295',
        year=2007,
        season=Season.SPRING,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=False,
    ),
    # ExamURL(  # TODO
    #     url=r'http://www.math.ntnu.no/emner/TMA4215/2012h/ovinger/ov06/ov06.pdf',
    #     code='TMA4215',
    #     year=2012,
    #     season=Season.AUTUMN,
    #     solutions=True,
    #     language=Language.BOKMAL,
    #     probably_exam=False,
    # ),
    ExamURL(
        url=r'http://www.math.ntnu.no/emner/TMA4240/eksamen/lsf/eksJun15l.pdf',
        code='TMA4240',
        year=2015,
        season=Season.SPRING,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(  # Physics exam archive link (exam)
        url=r'https://www.ntnu.no/documents/10422/1269546830/E-FY1001-14des2017.pdf/dc01118f-e932-46f4-a190-b262bcbcdb9a',
        code='FY1001',
        year=2017,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(  # Physics exam archive link (solutions)
        url=r'https://www.ntnu.no/documents/10422/1269546830/L-FY1001-14des2017.pdf/59fdc68d-2469-47c2-936d-3e21b7a68287',
        code='FY1001',
        year=2017,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269547939/L-FY2045-00aug2015.pdf/d4ee89d2-5285-4b4b-9b0c-21e9be70bfc7',
        code='FY2045',
        year=2015,
        season=Season.CONTINUATION,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1270776078/E-74350-24nov1999-eng.pdf/5f88d27d-38bb-40d8-a51b-24462697088a',
        code='74350',
        year=1999,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.ENGLISH,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269547939/E_FY2045_14des2017.pdf/03a3239f-1570-447f-9f70-b8310982851c">E-FY2045-14des2017',
        code='FY2045',
        year=2017,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269547939/EL-FY2045-06des2016.pdf/5c135a5e-17a7-45ec-ad0c-415a0d3ae373',
        code='FY2045',
        year=2016,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(  # TODO: Fix content type here
        url=r'https://www.ntnu.no/documents/10422/1269547939/TYPOS-FY2045-06des2016.pdf/8e70fe81-b025-4819-8518-c7f24ab3db31',
        code='FY2045',
        year=2016,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269549900/E-FY3464-11mar2013.pdf/9153c5d0-4446-4a91-8a65-a4e9b238bde0',
        code='FY3464',
        year=2013,
        season=Season.SPRING,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1270777388/E-FY3404-13okt2005.pdf/6201b017-f410-4232-a957-59605eef4f6b',
        code='FY3404',
        year=2005,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269550455/L-TFY4104-18des2014a.pdf/df99b55b-13ae-4335-ad3c-8773fd985b7a',
        code='TFY4104',
        year=2014,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269550731/L-TFY4106-17des2014-mc38IJ49.pdf/4ea06378-95fa-4b1e-a5bb-f394aafa2fd6',
        code='TFY4106',
        year=2014,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269551364/Eks18augTFY4115.pdf/2b1b0da1-01c7-4239-a672-40e2b7a6f371',
        code='TFY4115',
        year=2018,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1269552156/eksamen_TFY4165_August_2017.pdf/84db3fa7-592e-4011-96b1-2dfd3ec5bd05',
        code='TFY4165',
        year=2017,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1270779225/E-SIF4016-30jul2001.pdf/3ecdf842-8336-4c84-994b-ac99ed24c03e',
        code='SIF4016',
        year=2001,
        season=Season.CONTINUATION,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1270666512/E-TFY4205-26feb2008.pdf/afbeb4e1-7e58-4f9a-9b74-897444cd1905',
        code='TFY4205',
        year=2008,
        season=Season.SPRING,
        solutions=False,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    ExamURL(
        url=r'https://www.ntnu.no/documents/10422/1270794719/L-TFY4230-15aug2009_fk09.pdf/d55dfc3c-c463-45e6-b7db-e5fcb5d0df20',
        code='TFY4230',
        year=2009,
        season=Season.CONTINUATION,
        solutions=True,
        language=Language.BOKMAL,
        probably_exam=True,
    ),
    # ExamURL(  # TODO
    #     url=r'https://www.ntnu.no/documents/10422/1270656483/E-TFY4340-FY8909-24mai2017.pdf/90770b62-ac7f-406a-a29d-8303938cfdf6',
    #     code='FY8909',
    #     year=2017,
    #     season=Season.SPRING,
    #     solutions=False,
    #     language=Language.BOKMAL,
    #     probably_exam=True,
    # ),
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

    @pytest.mark.parametrize('exam', ExamURLs)
    def test_probably_exam(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.probably_exam == exam.probably_exam

    @pytest.mark.parametrize('exam', ExamURLs)
    def test_language_parser(self, exam):
        url_parser = ExamURLParser(url=exam.url)
        assert url_parser.language == exam.language


def test_tokenize():
    assert ExamURLParser.tokenize('abc') == 'abc'
    assert ExamURLParser.tokenize('TMA4215') == '_tma_4215'
    assert ExamURLParser.tokenize('eksMai18n') == 'eks_mai18n'
    assert (
        ExamURLParser.tokenize('LFeksamener2006-2010.pdf') ==
        '_lf_eksamener2006-2010.pdf'
    )


class ExamPDF:
    def __init__(
        self,
        pages: List[str],
        course_codes: List[str],
        year: int,
        season: Season,
        solutions: bool,
        language: Language,
        content_type: Optional[str],
    ):
        self.pages = pages
        self.course_codes = course_codes
        self.year = year
        self.season = season
        self.solutions = solutions
        self.language = language
        self.content_type = content_type

    def __repr__(self) -> str:
        return f'ExamPDF(text="""{self.pages[0]}""")'


ExamPDFs = [
    ExamPDF(
        pages=[
            """
            NTNU TMA4115 Matematikk 3
            Institutt for matematiske fag
            eksamen 11.08.05
            Løsningsforslag
            Eksamenssettet har 12 punkter.
            """,
        ],
        course_codes=['TMA4115'],
        year=2005,
        season=Season.CONTINUATION,
        solutions=True,
        language=Language.BOKMAL,
        content_type=DocumentInfo.EXAM,
    ),
    ExamPDF(
        pages=[
            """
            Eksamen i TMA4190 Mangfoldigheter
            fredag 30 mai, 2014
            LØYSINGSFORSLAG
            Oppgåve 1
            Vi de…nerer funksjonane F : R4 ! R2 og G : R2 ! R4 ved å sette...
            """,
        ],
        course_codes=['TMA4190'],
        year=2014,
        season=Season.SPRING,
        solutions=True,
        language=Language.NYNORSK,
        content_type=DocumentInfo.EXAM,
    ),
    ExamPDF(  # First in list of valid course codes
        pages=[
            """
            Eksamen TMA4122/23
            10. august 2009
            Løsningsforslag
            """,
        ],
        course_codes=['TMA4122', 'TMA4123'],
        year=2009,
        season=Season.CONTINUATION,
        solutions=True,
        language=Language.BOKMAL,
        content_type=DocumentInfo.EXAM,
    ),
    ExamPDF(  # Last in list of valid course codes
        pages=[
            """
            Eksamen TIØ4122/23
            10. august 2009
            Løsningsforslag
            """,
        ],
        course_codes=['TIØ4122', 'TIØ4123'],
        year=2009,
        season=Season.CONTINUATION,
        solutions=True,
        language=Language.BOKMAL,
        content_type=DocumentInfo.EXAM,
    ),
    ExamPDF(  # Middle of list of valid course codes
        pages=[
            """
            Eksamen TFY4122/23
            10. august 2009
            Løsningsforslag
            """,
        ],
        course_codes=['TFY4122', 'TFY4123'],
        year=2009,
        season=Season.CONTINUATION,
        solutions=True,
        language=Language.BOKMAL,
        content_type=DocumentInfo.EXAM,
    ),
    ExamPDF(  # Middle of list of valid course codes
        pages=["TMA4115 Calculus 3, Summer 2017, Solutions Page 1 of 6"],
        course_codes=['TMA4115'],
        year=2017,
        season=Season.CONTINUATION,
        solutions=True,
        language=Language.ENGLISH,
        content_type=DocumentInfo.UNDETERMINED,
    ),
    ExamPDF(  # Contains word solutions in problem discription
        pages=[
            """
            Norwegian University of Science and Technology         Page 1 of 2
            Department of Mathematical Sciences
            Contact during the exam: Hans Pettersen
            (Telephone 735 96688)
            EXAM IN MA1201 LINEAR ALGEBRA AND GEOMETRY
                                 Monday 3rd December 2007
                                   Time: kl. 09.00 - 13.00
                            Permitted aids: No permitted aids.
                                          English
            All answers must be justified. All problems will count the same
            when grading the exam.
            Grades: 21st December 2007.
            Problem 1
            a) We consider the following system of equations
                                      x + 2y − 3z = 1
                                    2x + y + 3αz = 2
                                    2x +              2z = β
            where α and β are constants. For what values of α and β does the
            system of equa-
            tions have
            (i) no solutions
            (ii) infinite number of solutions
            (iii) exactly one solution?
            """,
        ],
        course_codes=['MA1201'],
        year=2007,
        season=Season.AUTUMN,
        solutions=False,
        language=Language.ENGLISH,
        content_type=DocumentInfo.EXAM,
    ),
    ExamPDF(  # Contains course code with whitespace
        pages=[
            """
            TMA 4195 Mathematical Modeling,
            30 November 2006
            Solution with additional comments
            """
        ],
        course_codes=['TMA4195'],
        year=2006,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.ENGLISH,
        content_type=DocumentInfo.UNDETERMINED,
    ),
    ExamPDF(  # Contains specific solutions word 'løsning'
        pages=[
            """
            MATEMATISK MODELLERING (TMA4195)
            Eksamen torsdag 3. desember 2009
            Løsning med kommentarer
            """
        ],
        course_codes=['TMA4195'],
        year=2009,
        season=Season.AUTUMN,
        solutions=True,
        language=Language.BOKMAL,
        content_type=DocumentInfo.EXAM,
    ),
    ExamPDF(  # Contains specific solutions word 'Løsningsskisse'
        pages=[
            """
            TMA4245 Statistikk Eksamen juni 2015
            Norges teknisk-naturvitenskapelige universitet
            Institutt for matematiske fag Løsningsskisse Oppgave 1 a)
            På figuren er det vanskelig åse noen trend for
            samsvarende verdier for de to variablene X og Y .
            Variablene kan se ut som uavhengige. Derfor vil korrelasjon være
            (tilnærmet) 0. p p EX ≈ 2, Var(X) ≈ 1, EY ≈ 0, Var(Y ) ≈ 1.
            """
        ],
        course_codes=['TMA4245'],
        year=2015,
        season=Season.SPRING,
        solutions=True,
        language=Language.BOKMAL,
        content_type=DocumentInfo.EXAM,
    ),
]


class TestExamPdfParser:
    @pytest.mark.parametrize('pdf', ExamPDFs)
    def test_year_parsing(self, pdf):
        url_parser = PdfParser(text=pdf.pages[0])
        assert url_parser.year == pdf.year

    @pytest.mark.parametrize('pdf', ExamPDFs)
    def test_course_code_parsing(self, pdf):
        url_parser = PdfParser(text=pdf.pages[0])
        assert url_parser.course_codes == pdf.course_codes

    @pytest.mark.parametrize('pdf', ExamPDFs)
    def test_season_parser(self, pdf):
        url_parser = PdfParser(text=pdf.pages[0])
        assert url_parser.season == pdf.season

    @pytest.mark.parametrize('pdf', ExamPDFs)
    def test_solutions_parser(self, pdf):
        url_parser = PdfParser(text=pdf.pages[0])
        assert url_parser.solutions == pdf.solutions

    @pytest.mark.parametrize('pdf', ExamPDFs)
    def test_content_type(self, pdf):
        url_parser = PdfParser(text=pdf.pages[0])
        assert url_parser.content_type == pdf.content_type

    @pytest.mark.parametrize('pdf', ExamPDFs)
    def test_language_parser(self, pdf):
        url_parser = PdfParser(text=pdf.pages[0])
        assert url_parser.language == pdf.language
