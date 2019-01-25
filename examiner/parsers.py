import logging
import re
from typing import List, Optional, Tuple

from django.utils.encoding import uri_to_iri


logger = logging.getLogger()


COURSE_LETTERS = [
    'BI',
    'FI',
    'FY',
    'HLS',
    'IT',
    'KJ',
    'KULT',
    'MA',
    'MFEL',
    'PSY',
    'TBT',
    'TDT',
    'TFE',
    'TFY',
    'TGB',
    'TIØ',
    'TKT',
    'TMA',
    'TMM',
    'TMT',
    'TT',
    'TTK',
    'TTM',
    'TTT',
]


class Season:
    """
    The season when the exam took place.

    These are the values that are stored to the database.
    """

    SPRING = 1
    CONTINUATION = 2
    AUTUMN = 3
    UNKNOWN = None

    @classmethod
    def str_from_field(cls, name):
        if name == cls.SPRING:
            return 'Vår'
        elif name == cls.CONTINUATION:
            return 'Kont'
        elif name == cls.AUTUMN:
            return 'Høst'
        else:
            return 'Ukjent'


class Language:
    """
    The written language of the exam.

    These are the values that are stored to the database.
    """

    BOKMAL = 'Bokmål'
    NYNORSK = 'Nynorsk'
    ENGLISH = 'Engelsk'
    UNKNOWN = None


class ExamURLParser:
    """
    Retrieve information from exam PDF URL.

    :param url: Full URL pointing to http(s) hosted exam PDF file.
    """
    COURSE_PATTERNS = r'(?:' + '|'.join(COURSE_LETTERS) + r') ?\d\d\d\d'
    AUTUM_SEASONS = (
        'h',
        'des',
        'desember',
        'dec',
        'december',
        'nov',
        'november',
        'hoest',
    )
    SPRING_SEASONS = ('v', 'jun', 'juni', 'june', 'mai', 'may', 'vaar')
    CONTINUATION_SEASONS = ('k', 'kont', 'continuation')

    def __init__(self, url: str) -> None:
        """Constructor for ExamURLParser."""
        self.url = url
        self.code = self._code(self.url)
        self.parsed_url = self.tokenize(uri_to_iri(url))

        if self.code:
            self.parsed_url = self.parsed_url.replace(self.code, '')

        self.filename = uri_to_iri(url).rsplit('/')[-1]
        self.parsed_filename = self.tokenize(
            uri_to_iri(self.parsed_url).rsplit('/')[-1],
        )

        parts = uri_to_iri(self.parsed_url).rsplit('/')
        self.parsed_filename = self.tokenize(parts[-1])

        # Check if filename is not at the end of the URL
        if parts[-1][-4:].lower() != '.pdf':
            for part in parts:
                if part[-4:].lower() == '.pdf':
                    self.parsed_filename = part

        if url[:30] == 'https://www.ntnu.no/documents/':
            # Special case for physics exam URL which is easy to parse
            if self.parse_physics_url():
                return

        # First try to retrieve information from solely the filename
        self._year, self._season = self.find_date(string=self.parsed_filename)

        # If unsucessful, try with the entire URL instead
        if self._year is None or self._season is None:
            year, season = self.find_date(string=self.parsed_url)
            self._year = self._year or year
            self._season = self._season or season
        else:
            # Year and season given in filename, so probably an exam
            self._probably_exam = True

        self._season = self._season or Season.UNKNOWN

        if self.continuation:
            self._season = Season.CONTINUATION

    @staticmethod
    def tokenize(string: str) -> str:
        s1 = re.sub('([^A-Z]*)([A-Z]{2,})([^A-Z]*)', r'\1_\2_\3', string)
        s2 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s1)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s2).lower()

    @classmethod
    def find_date(cls, string: str) -> Tuple[Optional[int], Optional[Season]]:
        """
        Return year and season of exam from string identifier.

        :param string: String (URL) identifying the exam PDF.
        :return: 2-tuple (year, season).
        """

        nondigit = r'[\D]'
        full_year = r'(?P<year>(?:19[6-9][0-9]|20[0-2][0-9]))'
        month = '(?P<month>[0-1][0-9])'
        day_num = r'(?:[\D][0-3][0-9])?'

        # Check if full date pattern is available
        full_date = (nondigit + full_year + nondigit + month + day_num)
        matches = list(re.finditer(full_date, string))
        if matches:
            match = matches[-1]
            year = int(match.group('year'))
            month = int(match.group('month'))
            if month <= 6:
                season = Season.SPRING
            elif month >= 9:
                season = Season.AUTUMN
            else:
                season = Season.CONTINUATION
            return year, season

        abbreviated_year = r'(?P<year>[0-1][0-9])'
        season_str = (
            r'(?P<season>' +
            '|'.join(
                cls.AUTUM_SEASONS +
                cls.SPRING_SEASONS +
                cls.CONTINUATION_SEASONS
            ) +
            ')'
        )

        # All the different permutations available to us
        nonchar = '[^a-z]'
        specific_date_patterns = [
            re.compile(nondigit + full_year + season_str),
            re.compile(nonchar + season_str + full_year + nondigit),
            re.compile(nondigit + abbreviated_year + season_str),
            re.compile(nonchar + season_str + abbreviated_year + nondigit),
            re.compile(nondigit + full_year + nondigit),
            re.compile(nondigit + abbreviated_year + nondigit),
        ]

        # Check if any of these patterns match
        for specific_date_pattern in specific_date_patterns:
            matches = list(re.finditer(specific_date_pattern, string))
            if matches:
                match = matches[-1]
                season = match.groupdict().get('season')
                year = match.groupdict().get('year')
                break
        else:
            return None, None

        if len(year) == 2:
            year = '20' + year
        year = int(year)

        if season:
            if season.lower() in cls.AUTUM_SEASONS:
                season = Season.AUTUMN
            elif season.lower() in cls.SPRING_SEASONS:
                season = Season.SPRING
            else:
                season = Season.CONTINUATION

        return year, season

    @classmethod
    def _code(cls, string: str) -> Optional[str]:
        """Return course code related to the URL."""
        code_pattern = re.compile(cls.COURSE_PATTERNS, re.IGNORECASE)
        code = code_pattern.findall(string)
        return code[-1].replace('_', '').upper() if code else None

    @property
    def year(self) -> Optional[int]:
        """Return original year of the exam URL."""

        if hasattr(self, '_year'):
            return self._year

        year_pattern = re.compile(
            r'(?:20[0-2][0-9]|19[7-9][0-9])',
            re.IGNORECASE,
        )
        year = year_pattern.findall(self.parsed_url)
        if year:
            self._year = int(year[-1])
            return self._year

        year_pattern = re.compile(r'[0-2][0-9]', re.IGNORECASE)
        year = year_pattern.findall(self.parsed_url)
        if year:
            self._year = int('20' + year[-1])
            return self._year

        self._year = None
        return self._year

    @property
    def solutions(self) -> bool:
        if hasattr(self, '_solutions'):
            return self._solutions

        solution_pattern = re.compile(
            r'(lf|lsf|losning|loesning|loys|fasit|solution|sol[^a-zA-Z])',
            re.IGNORECASE,
        )
        solution = solution_pattern.findall(self.parsed_url)
        self._solutions = bool(solution)
        return self._solutions

    @property
    def continuation(self) -> bool:
        """Return True if exam url points to solution set."""

        if hasattr(self, '_continuation'):
            return self._continuation

        kont_pattern = re.compile(r'(kont|aug)', re.IGNORECASE)
        kont = kont_pattern.findall(self.parsed_filename)
        self._continuation = bool(kont)
        return self._continuation

    @property
    def season(self) -> Season:
        """Return season string, either Season.AUTUMN or Season.SPRING."""
        if hasattr(self, '_season'):
            return self._season

        autumn_pattern = re.compile(
            r'(' + '|'.join(self.AUTUM_SEASONS) + '|\d\d\d\dh|\d\dh)',
            re.IGNORECASE,
        )
        autumn = autumn_pattern.findall(self.parsed_url)
        self._season = Season.AUTUMN if autumn else Season.SPRING
        return self._season

    @property
    def language(self) -> Language:
        """Return the language of the exam."""

        if hasattr(self, '_language'):
            return self._language

        non_letter = r'[^a-zA-Z]'
        english_words = '(?:' + '|'.join([
            'en',
            'sol',
            'dec',
            'may',
            'june',
            'exam',
            'summer',
            'autumn',
            'spring',
            'ex',
        ]) + ')'
        nynorsk_words = '(?:' + '|'.join([
            'nn',
            'nynorsk',
            'loys',
            'ny' + non_letter,
        ]) + ')'
        bokmal_words = '(?:' + '|'.join([
            'nb',
            'bm',
            'bok',
            'losning',
            'loosning',
            'loesning',
            'fasit',
            'nor',
            'mai',
            'juni',
            'des',
            'lf',
            'kont',
            'eksam',
            'eks' + non_letter,
            'no' + non_letter,
        ]) + ')'

        english = re.compile(non_letter + english_words, re.IGNORECASE)
        bokmal = re.compile(non_letter + bokmal_words, re.IGNORECASE)
        nynorsk = re.compile(non_letter + nynorsk_words, re.IGNORECASE)

        # Prevent nonletter requirement screwing up match in beginning
        filename = '/' + self.parsed_filename

        if re.search(english, filename):
            self._language = Language.ENGLISH
        elif re.search(nynorsk, filename):
            self._language = Language.NYNORSK
        elif re.search(bokmal, filename):
            self._language = Language.BOKMAL
        else:
            self._language = Language.UNKNOWN

        return self._language

    @property
    def probably_exam(self) -> bool:
        """Return True if the url probably points to an exam document."""
        if hasattr(self, '_probably_exam'):
            return self._probably_exam

        if self.continuation:
            self._probably_exam = True
            return self._continuation

        exam_pattern = re.compile(r'(?:eksam|exam|dvikan)', re.IGNORECASE)
        self._probably_exam = bool(re.search(exam_pattern, self.parsed_url))
        return self._probably_exam

    def parse_physics_url(self) -> bool:
        """
        Parse physics url.

        Physics URL have the following (example) format:
        <-e932-46f4-a190-b262bcbcdb9a/<id1>/<id2>/E-FY1001-14des2017.pdf/<id3>
        Which is an *E*xam for FY1001 on the 14th of december, 2017

        We can therefore hardcode parsing of such URLs. The exam is assumed
        to be Norwegian by default.

        :return: True if success, otherwise False.
        """
        # All such URLs represent Norwegian (Bokmål) exams
        self._probably_exam = True
        self._language = Language.BOKMAL

        filename = self.url.split('/')[-2].replace('.pdf', '')

        # Sometimes tokens are seperated with '_' instead of '-'
        splitter = '-' if '-' in filename else '_'
        try:
            solution, course, date, *language = filename.split(splitter)
        except ValueError:
            # Not properly formatted, fall back to ordinary parsing method
            return False

        self.code = course.upper()

        if solution.upper() in ('E', 'TYPOS'):
            self._solutions = False
        elif solution.upper() in ('L', 'EL'):
            self._solutions = True
        else:
            logger.error(f'Could not parse solutions for url {self.url}')
            return False

        try:
            self._year = int(re.search(r'(\d\d\d\d)', date).group(0))
        except AttributeError:
            logger.error(f'Could not parse year for url {self.url}')
            self._year = None

        if 'des' in date or 'nov' in date or 'jan' in date or 'okt' in date:
            self._season = Season.AUTUMN
        elif (
            'apr' in date
            or 'mai' in date
            or 'jun' in date
            or 'mar' in date
            or 'feb' in date
        ):
            self._season = Season.SPRING
        elif 'aug' in date or 'jul' in date:
            self._season = Season.CONTINUATION
        else:
            logger.error(f'Could not parse season for url {self.url}')

        if language:
            if 'eng' in language[0].lower():
                self._language = Language.ENGLISH
            else:
                logger.error(f'Could not parse language reminder {language}')

        return True

    def __repr__(self) -> str:
        """Return code string representation of Exam URL object."""
        return f'ExamURLParser(url={self.url})'

    def __str__(self) -> str:
        """Return string representation of Exam URL object."""
        return (
            f'{self.code or "Ukjent"} '
            f'{"LF" if self.solutions else "Eksamen"} '
            f'{self.year or "Ukjent"} {self.season} '
            f'({self.language or "Ukjent språk"})'
        )


NYNORSK_WORDS = [
    'nynorsk',
    'løysning',
    'oppgåve',
    'fagleg',
    'frå-til',
    'tillatne',
    'sidetal:',
    'ikkje',
]
NYNORSK_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(NYNORSK_WORDS) + r')\b',
    re.IGNORECASE,
)

BOKMAL_WORDS = [
    'bokmål',
    'eksamen',
    'løsning',
    'løsningsforslag',
    'løsningsskisse',
    'oppgave',
    'faglig',
    'fra-til',
    'tillate',
    'sidetall:',
]
BOKMAL_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(BOKMAL_WORDS) + r')\b',
    re.IGNORECASE,
)

ENGLISH_WORDS = [
    'english',
    'exam',
    'page',
    'fall',
    'solutions',
    'solution',
]
ENGLISH_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(ENGLISH_WORDS) + r')\b',
    re.IGNORECASE,
)


SPRING_WORDS = [
    r'mai',
    r'may',
    r'juni',
    r'june',
    r'spring',
]
SPRING_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(SPRING_WORDS) + r')\b',
    re.IGNORECASE,
)

CONTINUATION_WORDS = [r'august', r'summer']
CONTINUATION_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(CONTINUATION_WORDS) + r')\b',
    re.IGNORECASE,
)

AUTUMN_WORDS = [
    r'december',
    r'desember',
    r'november',
    r'autumn',
    r'januar',
    r'january',
    r'fall',
]
AUTUMN_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(AUTUMN_WORDS) + r')\b',
    re.IGNORECASE,
)

EXAM_WORDS = [
    r'eksamen',
    r'exam',
    r'examination',
]
EXAM_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(EXAM_WORDS) + r')\b',
    re.IGNORECASE,
)

SOLUTIONS_WORDS = [
    r'LF',
    r'løsningsforslag',
    r'løysingsforslag',
    r'løsningsskisse',
    r'løsning',
    r'solution',
    r'solutions',
]
SOLUTIONS_WORDS_PATTERN = re.compile(
    r'\b(' + r'|'.join(SOLUTIONS_WORDS) + r')\b',
    re.IGNORECASE,
)

COMBINING_COURSE = r'(?:/(\d{1,4}))?'   # e.g. TMA4123/24
COURSE_CODES_PATTERN = re.compile(
    r'((?:' + r'|'.join(COURSE_LETTERS) + r') ?\d{3,4})' + COMBINING_COURSE,
    re.IGNORECASE,
)

YEAR_PATTERN = re.compile(r'\b((?:20[0-2][0-9]|19[7-9][0-9]))\b')
DATE_PATTERN = re.compile(
    r'(?P<day>[0-3][0-9])'
    r'(?:\.|/)'
    r'(?P<month>[0-1][0-9])'
    r'(?:\.|/)'
    r'(?P<year>[9012][0-9])',
)

PROBLEMS_BEGINNING_WORDS = [
    r'^\s*problem 1a?\)?',
    r'^\s*task 1a?\)?',
    r'^\s*oppgave 1a?\)?',
    r'^\s*oppgåve 1a?\)?',
    r'^\s*\ba\)',
]
PROBLEMS_BEGINNING_PATTERN = re.compile(
    r'(?:' + r'|'.join(PROBLEMS_BEGINNING_WORDS) + r')',
    re.IGNORECASE | re.MULTILINE,
)


class PdfParser:
    """
    Naive PDF content classifier.

    The class uses simple regexes in order to determine the content of a PDF,
    focusing on determining which Exam model object should be connected to
    the Pdf model object.
    """

    def __init__(self, text: str) -> None:
        """Constructor for PDF parser."""
        # Find the text that occurs before the first problem, for now only
        # used for finding if the exam set contains solutions. This is important
        # because problems will often mentoin "find the solutions...".
        problems_beginning = re.search(PROBLEMS_BEGINNING_PATTERN, text)
        if problems_beginning:
            entry_text = text[:problems_beginning.span()[0] + 1]
        else:
            entry_text = text

        self.content_type = self._content_type(text=text)
        self.course_codes = self._course_codes(text=text)
        self.language = self._language(text=text)
        self.year, self.season = self._date(text=text)
        self.solutions = self._solutions(text=entry_text)

    def _content_type(cls, text: str) -> Optional[str]:
        """Return True if the text probably is related to an exam."""
        from examiner.models import DocumentInfo
        if bool(re.search(EXAM_WORDS_PATTERN, text)):
            return DocumentInfo.EXAM
        else:
            return DocumentInfo.UNDETERMINED

    def _solutions(cls, text: str) -> bool:
        """Return True if the text probably contains solutions."""
        return bool(re.search(SOLUTIONS_WORDS_PATTERN, text))

    @classmethod
    def _course_codes(cls, text: str) -> List[str]:
        """Return course codes present in the text."""
        course_codes = []
        for match in re.finditer(COURSE_CODES_PATTERN, text):
            # E.g. TMA4123
            primary = match.group(1).upper().replace(' ', '')
            course_codes.append(primary)

            if match.group(2) is None:
                continue

            # E.g. TMA4123/24 -> TMA4124
            secondary = match.group(2).upper()
            try:
                course_codes.append(primary[:-len(secondary)] + secondary)
            except IndexError:
                pass

        return course_codes

    @classmethod
    def _language(cls, text: str) -> Language:
        """Return Language of the text."""
        if re.search(NYNORSK_WORDS_PATTERN, text):
            return Language.NYNORSK
        elif re.search(ENGLISH_WORDS_PATTERN, text):
            return Language.ENGLISH
        elif re.search(BOKMAL_WORDS_PATTERN, text):
            return Language.BOKMAL
        else:
            return Language.UNKNOWN

    @classmethod
    def _date(cls, text: str) -> Tuple[int, Season]:
        """Return year and season of the text."""
        if re.search(SPRING_WORDS_PATTERN, text):
            season = Season.SPRING
        elif re.search(CONTINUATION_WORDS_PATTERN, text):
            season = Season.CONTINUATION
        elif re.search(AUTUMN_WORDS_PATTERN, text):
            season = Season.AUTUMN
        else:
            season = Season.UNKNOWN

        year = re.search(YEAR_PATTERN, text)
        if year:
            year = int(year.group(0))

        if not year or not season:
            date_match = re.search(DATE_PATTERN, text)
            if not date_match:
                return year, season

            if not year:
                year = date_match.group('year')
                if int(year[0]) in (0, 1, 2):
                    year = int('20' + year)
                else:
                    year = int('19' + year)

            if not season:
                month = int(date_match.group('month'))
                if month in (1, 10, 11, 12):
                    season = Season.AUTUMN
                elif month in (7, 8, 9):
                    season = Season.CONTINUATION
                elif month in (4, 5, 6):
                    season = Season.SPRING
                else:
                    season = Season.UNKNOWN

        return year, season

    def __repr__(self) -> str:
        return (
            '<Exam '
            f"course_code='{self.course_codes}' "
            f'year={self.year} '
            f'season={self.season} '
            f'language={self.language} '
            f'solutions={self.solutions} '
            f'content_type={self.content_type}'
            '>'
        )
