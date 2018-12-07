from django.shortcuts import render

from examiner.crawlers import MathematicalSciencesCrawler
from examiner.models import ExamURL
from semesterpage.models import Course


def all_exams(request):
    exam_urls = (
        ExamURL
        .objects
        .filter(
            year__isnull=False,
            probably_exam=True,
        )
        .order_by('course_code', '-year', '-solutions')
    )
    context = {
        'exam_urls': exam_urls,
        'header_text': f' / exams',
        'user': request.user,
    }
    return render(request, 'examiner/home.html', context)


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
        .filter(
            course_code__iexact=course_code,
            year__isnull=False,
            probably_exam=True,
        )
        .order_by('course_code', '-year', '-solutions')
    )
    context = {
        'exam_urls': exam_urls,
        'course_code': course_code.upper(),
    }
    return render(request, 'examiner/home.html', context)
