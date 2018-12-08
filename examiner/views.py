from django.db.models import F
from django.shortcuts import render

from examiner.crawlers import MathematicalSciencesCrawler
from examiner.models import ExamURL
from semesterpage.models import Course


def all_exams(request):
    exam_urls = (
        ExamURL
        .objects
        .order_by(
            F('course_code'),
            F('year').desc(nulls_last=True),
            F('solutions').desc(),
        )
    )
    context = {
        'exam_courses': exam_urls.organize(),
        'header_text': f' / exams',
        'user': request.user,
    }
    return render(request, 'examiner/exam_archive.html', context)


def crawl(request):
    tma_courses = Course.objects.filter(course_code__startswith='TMA')
    tma_crawlers = MathematicalSciencesCrawler(courses=tma_courses)
    for crawler in tma_crawlers:
        for url in crawler.pdf_urls():
            exam_url, _ = ExamURL.objects.get_or_create(url=url)
            exam_url.parse_url()
            exam_url.save()

    return all_exams(request)


def course(request, course_code: str):
    exam_urls = (
        ExamURL
        .objects
        .filter(course_code__iexact=course_code)
        .order_by(
            F('course_code'),
            F('year').desc(nulls_last=True),
            F('solutions').desc(),
        )
    )
    context = {
        'exam_courses': exam_urls.organize(),
        'course_code': course_code.upper(),
        'header_text': f' / exams / ' + course_code,
        'user': request.user,
    }
    return render(request, 'examiner/exam_archive.html', context)
