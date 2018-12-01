import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup as bs

from django.http import HttpResponse
from django.shortcuts import render

import requests

from examiner.parsers import ExamURLParser
from semesterpage.models import Course


# Create your views here.
def test(request):
    tma_courses = Course.objects.filter(course_code__startswith='TMA')
    tma_crawlers = TMACrawlers(courses=tma_courses)
    context = {'crawlers': tma_crawlers}
    return render(request, 'examiner/home.html', context)


class TMACrawlers:
    def __init__(self, courses):
        self.courses = [TMACrawler(code=course.course_code) for course in courses]

    def __iter__(self):
        return (course for course in self.courses if course)


class TMACrawler:
    WIKI_URL = 'https://wiki.math.ntnu.no/'

    def __init__(self, code: str) -> None:
        self.code = code

    @property
    def homepage_url(self) -> str:
        return self.WIKI_URL + self.code

    @property
    def has_content(self) -> bool:
        response = requests.get(self.homepage_url)
        if not response.ok:
            return False
        return True

    def exams_page(self):
        response = requests.get(self.homepage_url)
        soup = bs(response.content, 'html.parser')
        latest = soup.find('a', text=re.compile('^.*20\d\d.*$'), href=True)
        if not latest:
            return ''

        latest = urljoin(self.WIKI_URL, latest['href'])
        response = requests.get(latest)
        soup = bs(response.content, 'html.parser')
        patterns = (
            r'old exams',
            r'gamle eksamensoppgaver',
            r'eksamensoppgaver',
            r'tidligere eksamener',
            r'earlier exams',
            r'old exam sets',
            r'eksamenssett',
        )
        for pattern in patterns:
            link = soup.find(
                'a',
                text=re.compile(pattern, re.IGNORECASE),
                href=True,
            )
            if link:
                return urljoin(self.WIKI_URL, link['href'])

        return self.homepage_url


    def pdf_urls(self):
        exams_url = self.exams_page()
        if not exams_url:
            return []
        response = requests.get(exams_url)
        soup = bs(response.content, 'html.parser')
        links = soup.find_all('a')
        return [
            ExamURLParser(urljoin(self.WIKI_URL, link.get('href')))
            for link
            in links
            if link.get('href') and link.get('href').endswith('.pdf')
        ]

    def __str__(self) -> str:
        return self.code

    def __bool__(self) -> bool:
        return self.has_content
