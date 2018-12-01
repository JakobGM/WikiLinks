import re
from typing import Optional, Tuple

from django.utils.encoding import uri_to_iri


class ExamURLParser:
    def __init__(self, url: str) -> None:
        self.url = url
        self.parsed_url = uri_to_iri(url)
        self.parsed_url = self.parsed_url.replace(self.code, '')
        self.filename = uri_to_iri(url).rsplit('/')[-1]

        self._year, self._season = self.find_date(string=self.filename)
        if self._year is None or self._season is None:
            year, season = self.find_date(string=self.parsed_url)
            self._year = self._year or year
            self._season = self._season or season

        self._season = self._season or 'Ukjent'

        if self.continuation:
            self._season = 'Kontinuasjonseksamen'

    def find_date(self, string) -> Tuple[Optional[int], Optional[str]]:
        nondigit = '[\D]'

        # Check if full date pattern is available
        full_year = r'(?P<year>(?:19[6-9][0-9]|20[0-2][0-9]))'
        full_date = (
            nondigit +
            full_year +
            nondigit +
            '(?P<month>[0-1][0-9])' +
            '(?:[\D][0-3][0-9])?'
        )
        re.compile(full_date)
        matches = list(re.finditer(full_date, string))
        if matches:
            match = matches[-1]
            year = int(match.group('year'))
            month = int(match.group('month'))
            if month <= 6:
                season = 'Vår'
            elif month >= 9:
                season = 'Høst'
            else:
                season = 'Kontinuasjonseksamen'
            return year, season

        abbreviated_year = r'(?P<year>[0-1][0-9])'
        season_str = r'(?P<season>h|des|desember|dec|december|nov|november|v|jun|juni|june|mai|may|k)'

        specific_date_patterns = [
            re.compile(nondigit + full_year + season_str, re.IGNORECASE),
            re.compile(season_str + full_year + nondigit, re.IGNORECASE),
            re.compile(nondigit + abbreviated_year + season_str, re.IGNORECASE),
            re.compile(season_str + abbreviated_year + nondigit, re.IGNORECASE),
            re.compile(nondigit + full_year + nondigit, re.IGNORECASE),
            re.compile(nondigit + abbreviated_year + nondigit, re.IGNORECASE),
        ]
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
            if season.lower() in (
                'h',
                'des',
                'desember',
                'dec',
                'december',
                'nov',
                'november',
            ):
                season = 'Høst'
            elif season.lower() == 'k':
                season = 'Kontinuasjonseksamen'
            else:
                season = 'Vår'

        return year, season


    @property
    def code(self):
        code_pattern = re.compile(r'TMA\d\d\d\d', re.IGNORECASE)
        code = code_pattern.findall(self.url)
        if code:
            return code[-1].upper()
        return ''

    @property
    def year(self) -> int:
        if hasattr(self, '_year'):
            return self._year

        year_pattern = re.compile(r'20\d\d', re.IGNORECASE)
        year = year_pattern.findall(self.parsed_url)
        if year:
            self._year = int(year[-1])
            return self._year

        year_pattern = re.compile(r'\d\d', re.IGNORECASE)
        year = year_pattern.findall(self.parsed_url)
        if year:
            self._year = int('20' + year[-1])
            return self._year

        self._year = 0
        return self._year

    @property
    def solutions(self) -> bool:
        solution_pattern = re.compile(r'(lf|losning|solution|sol[^a-zA-Z])', re.IGNORECASE)
        solution = solution_pattern.findall(self.filename)
        if solution:
            return True
        return False

    @property
    def continuation(self) -> bool:
        kont_pattern = re.compile(r'(kont|aug)', re.IGNORECASE)
        kont = kont_pattern.findall(self.filename)
        if kont:
            return True
        return False

    @property
    def season(self) -> str:
        if hasattr(self, '_season'):
            return self._season

        autumn_pattern = re.compile(r'(autumn|dec|nov|\d\d\d\dh|\d\dh)', re.IGNORECASE)
        autumn = autumn_pattern.findall(self.parsed_url)
        if autumn:
            self._season = 'Høst'
        else:
            self._season = 'Vår'

        return self._season

    def __repr__(self) -> str:
        return f'ExamURLParser(url={self.url})'

    def __str__(self) -> str:
        string = f'{self.code} - {self.year} {self.season}'
        if self.solutions:
            string += ' (LF)'
        return string

        name.append(self.url)
        return ' - '.join(name)
