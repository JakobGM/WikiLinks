import re
from typing import Iterable, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup as bs

import requests

from semesterpage.models import Course


class MathematicalSciencesCrawler:
    """
    Crawler for courses at the Department for Mathematical Sciences.

    It will only find content on wiki.math.ntnu.no/{course.course_code}.
    """

    def __init__(self, courses: Iterable[Course]) -> None:
        self.crawlers = [
            MathematicalSciencesCourseCrawler(code=course.course_code)
            for course
            in courses
        ]

    def __iter__(self):
        return (crawler for crawler in self.crawlers if crawler)


class MathematicalSciencesCourseCrawler:
    WIKI_URL = 'https://wiki.math.ntnu.no/'

    def __init__(self, code: str) -> None:
        self.code = code

    @property
    def homepage_url(self) -> str:
        return self.WIKI_URL + self.code

    @property
    def has_content(self) -> bool:
        try:
            response = requests.get(self.homepage_url)
        except Exception:
            return False
        if not response.ok:
            return False
        return True

    def exams_pages(self) -> str:
        try:
            response = requests.get(self.homepage_url, timeout=2)
        except Exception:
            return []
        if not response.ok:
            return []

        soup = bs(response.content, 'html.parser')
        years = soup.find_all(
            'a',
            text=re.compile(r'^.*(?:20[0-2]\d|199\d).*$'),
            href=True,
        )
        if not years:
            return []

        years = [
            urljoin(self.WIKI_URL, year['href'])
            for year
            in years
        ]
        result = set()

        for year in years:
            try:
                response = requests.get(year, timeout=2)
            except Exception:
                continue
            if not response.ok:
                continue

            soup = bs(response.content, 'html.parser')
            patterns = r'(?:' + r'|'.join([
                r'old exams',
                r'gamle eksamensoppgaver',
                r'eksamensoppgaver',
                r'tidligere eksamener',
                r'earlier exams',
                r'old exam sets',
                r'eksamenssett',
            ]) + r')'
            link = soup.find(
                'a',
                text=re.compile(patterns, re.IGNORECASE),
                href=True,
            )
            if link:
                result.add(urljoin(self.WIKI_URL, link['href']))
            else:
                result.add(self.homepage_url)

        return list(result)

    def pdf_urls(self) -> List[str]:
        exams_urls = self.exams_pages()
        if not exams_urls:
            return []

        result = set()

        for exams_url in exams_urls:
            try:
                response = requests.get(exams_url, timeout=2)
            except Exception:
                continue
            if not response.ok:
                continue

            soup = bs(response.content, 'html.parser')
            links = soup.find_all('a')
            for link in links:
                if link.get('href') and link.get('href').endswith('.pdf'):
                    result.add(urljoin(self.WIKI_URL, link.get('href')))

        return list(result)

    def __str__(self) -> str:
        return self.code

    def __bool__(self) -> bool:
        return self.has_content
