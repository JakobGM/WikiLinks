from enum import Enum
import re
from typing import Optional, Tuple

from django.utils.encoding import uri_to_iri


class ChoicesEnum(Enum):

    @classmethod
    def str_from_field(cls, field: str):
        key = field.split('.')[1]
        return cls[key].value or 'Ukjent'


class Season(ChoicesEnum):
    """Exam season type."""

    SPRING = 'Vår'
    AUTUMN = 'Høst'
    CONTINUATION = 'Kontinuasjonseksamen'
    UNKNOWN = None


class Language(ChoicesEnum):
    """The written language of the exam."""

    BOKMAL = 'Bokmål'
    NYNORSK = 'Nynorsk'
    ENGLISH = 'English'
    UNKNOWN = None


class ExamURLParser:
    """
    Retrieve information from exam PDF URL.

    :param url: Full URL pointing to http(s) hosted exam PDF file.
    """
    COURSE_PATTERNS = r'(?:TMA|TFY)\d\d\d\d'
    AUTUM_SEASONS = (
        'h',
        'des',
        'desember',
        'dec',
        'december',
        'nov',
        'november',
    )
    SPRING_SEASONS = ('v', 'jun', 'juni', 'june', 'mai', 'may')
    CONTINUATION_SEASONS = ('k', 'kont', 'continuation')

    def __init__(self, url: str) -> None:
        """Constructor for ExamURLParser."""

        self.url = url
        self.parsed_url = uri_to_iri(url)

        if self.code:
            self.parsed_url = self.parsed_url.replace(self.code, '')

        self.filename = uri_to_iri(url).rsplit('/')[-1]
        self.parsed_filename = uri_to_iri(self.parsed_url).rsplit('/')[-1]

        # First try to retrieve information from solely the filename
        self._year, self._season = self.find_date(string=self.filename)

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

    def find_date(self, string: str) -> Tuple[Optional[int], Optional[Season]]:
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
                self.AUTUM_SEASONS +
                self.SPRING_SEASONS +
                self.CONTINUATION_SEASONS
            ) +
            ')'
        )

        # All the different permutations available to us
        specific_date_patterns = [
            re.compile(nondigit + full_year + season_str, re.IGNORECASE),
            re.compile(season_str + full_year + nondigit, re.IGNORECASE),
            re.compile(nondigit + abbreviated_year + season_str, re.IGNORECASE),
            re.compile(season_str + abbreviated_year + nondigit, re.IGNORECASE),
            re.compile(nondigit + full_year + nondigit, re.IGNORECASE),
            re.compile(nondigit + abbreviated_year + nondigit, re.IGNORECASE),
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
            if season.lower() in self.AUTUM_SEASONS:
                season = Season.AUTUMN
            elif season.lower() in self.SPRING_SEASONS:
                season = Season.SPRING
            else:
                season = Season.CONTINUATION

        return year, season


    @property
    def code(self) -> Optional[str]:
        """Return course code related to the URL."""

        if hasattr(self, '_code'):
           return self._code

        code_pattern = re.compile(self.COURSE_PATTERNS, re.IGNORECASE)
        code = code_pattern.findall(self.url)
        self._code = code[-1].upper() if code else None
        return self._code

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
        solution_pattern = re.compile(
            r'(lf|losning|loesning|fasit|solution|sol[^a-zA-Z])',
            re.IGNORECASE,
        )
        solution = solution_pattern.findall(self.filename)
        if solution:
            return True
        return False

    @property
    def continuation(self) -> bool:
        """Return True if exam url points to solution set."""

        if hasattr(self, '_continuation'):
            return self._continuation

        kont_pattern = re.compile(r'(kont|aug)', re.IGNORECASE)
        kont = kont_pattern.findall(self.filename)
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
            'loysning',
        ]) + ')'
        bokmal_words = '(?:' + '|'.join([
            'nb',
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
            non_letter + 'no' + non_letter,
        ]) + ')'

        english = re.compile(non_letter + english_words, re.IGNORECASE)
        bokmal = re.compile(non_letter + bokmal_words, re.IGNORECASE)
        nynorsk = re.compile(non_letter + nynorsk_words, re.IGNORECASE)

        # Prevent nonletter requirement screwing up match in beginning
        filename = '/' + self.filename

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

        exam_pattern = re.compile(r'(?:eksam|exam)', re.IGNORECASE)
        self._probably_exam = bool(re.search(exam_pattern, self.parsed_url))
        return self._probably_exam

    def __repr__(self) -> str:
        """Return code string representation of Exam URL object."""
        return f'ExamURLParser(url={self.url})'

    def __str__(self) -> str:
        """Return string representation of Exam URL object."""
        return (
            f'{self.code or "Ukjent"} '
            f'{"LF" if self.solutions else "Eksamen"} '
            f'{self.year or "Ukjent"} {self.season.value} '
            f'({self.language.value or "Ukjent språk"})'
        )
