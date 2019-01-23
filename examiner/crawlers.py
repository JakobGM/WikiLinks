import re
from typing import Iterable, List, Optional
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
            patterns = r'.*(?:' + r'|'.join([
                r'exam',
                r'eksam',
            ]) + r').*'
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
            if exams_url[-4:] == '.pdf':
                # This is PDF so we can add it directly to the results
                result.add(exams_url)
                continue
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

    def __repr__(self) -> str:
        return f"MathematicalSciencesCourseCrawler(code='{self.code}')"

    def __bool__(self) -> bool:
        return self.has_content


class DvikanCrawler:
    """Crawler for for dvikan.no exam PDFs."""

    BASE_URL = 'https://dvikan.no/gamle-ntnu-eksamener/'

    @classmethod
    def course_urls(cls) -> Iterable[str]:
        """Get all course subfolders."""
        response = cls.get(cls.BASE_URL)
        if not response:
            return []

        soup = bs(response.content, 'html.parser')
        links = soup.find_all('a')
        return (
            cls.BASE_URL + link.get('href')
            for link
            in links
            if link.get('href') != 'https://dvikan.no'
            and link.get('href', 'x')[-1] == '/'
        )

    @classmethod
    def pdf_urls(cls) -> Iterable[str]:
        """Get all hosted PDFs from dvikan.no/gamle-ntnu-eksamener."""
        for course_url in cls.course_urls():
            response = cls.get(course_url)
            if not response:
                continue

            soup = bs(response.content, 'html.parser')
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
            for pdf_link in pdf_links:
                yield urljoin(course_url, pdf_link.get('href'))
        return

    @staticmethod
    def get(url: str) -> Optional[requests.models.Response]:
        """Get URL content with exception safeguarding."""
        try:
            return requests.get(url, timeout=10)
        except Exception:
            return None


class PhysicsCrawler:
    """Crawler for exams in the Physics Department exam archive."""

    BASE_URL = 'https://www.ntnu.no/fysikk/eksamen'

    @classmethod
    def course_urls(cls) -> Iterable[str]:
        """Get all physics courses hosted in the exam archive."""
        response = cls.get(cls.BASE_URL)
        if not response:
            return []

        soup = bs(response.content, 'html.parser')
        links = soup.select('div.asset-abstract h3.asset-title a')
        return (urljoin(cls.BASE_URL, link.get('href')) for link in links)

    @classmethod
    def pdf_urls(cls) -> Iterable[str]:
        """Get all hosted PDFs from Physics exam archive for course."""
        for course_url in cls.course_urls():
            response = cls.get(course_url)
            if not response:
                continue

            soup = bs(response.content, 'html.parser')
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf'))
            for pdf_link in pdf_links:
                yield urljoin(cls.BASE_URL, pdf_link.get('href'))
        return

    @staticmethod
    def get(url: str) -> Optional[requests.models.Response]:
        """Get URL content with exception safeguarding."""
        try:
            return requests.get(url, timeout=2)
        except Exception:
            return None
