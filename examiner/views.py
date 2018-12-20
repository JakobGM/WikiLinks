from typing import Optional

from django.db.models import F
from django.shortcuts import render

from examiner.crawlers import MathematicalSciencesCrawler
from examiner.models import Pdf, PdfUrl
from semesterpage.models import Course


def crawl(request):
    tma_courses = Course.objects.filter(course_code__startswith='TMA')
    tma_crawlers = MathematicalSciencesCrawler(courses=tma_courses)
    for crawler in tma_crawlers:
        for url in crawler.pdf_urls():
            exam_url, _ = PdfUrl.objects.get_or_create(url=url)
            exam_url.parse_url()
            exam_url.save()

    return exams(request)


def backup(request, course_code: str):
    exam_urls = PdfUrl.objects.filter(course_code__iexact=course_code)
    for exam_url in exam_urls:
        exam_url.backup_file()
    return exams(request)


def parse(request):
    exam_urls = PdfUrl.objects.all()
    for exam_url in exam_urls:
        exam_url.parse_url()
        exam_url.save()

    file_backups = Pdf.objects.filter(text__isnull=True)
    for file_backup in file_backups:
        file_backup.read_text()
        file_backup.save()
    return exams(request)


def exams(request, course_code: Optional[str] = None):
    exam_urls = (
        PdfUrl
        .objects
        .order_by(
            F('course_code'),
            F('year').desc(nulls_last=True),
            F('solutions').desc(),
        )
    )
    if course_code:
        exam_urls = exam_urls.filter(
            course_code__iexact=course_code.upper(),
        )

    context = {
        'exam_courses': exam_urls.organize(),
        'user': request.user,
    }
    if course_code:
        context['header_text'] = f' / exams / ' + course_code
    else:
        context['header_text'] = ' / exams'

    return render(request, 'examiner/exam_archive.html', context)
