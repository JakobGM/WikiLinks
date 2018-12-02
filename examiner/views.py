from django.shortcuts import render

from examiner.crawlers import MathematicalSciencesCrawler
from semesterpage.models import Course


def test(request):
    tma_courses = Course.objects.filter(course_code__startswith='TMA')
    tma_crawlers = MathematicalSciencesCrawler(courses=tma_courses)
    context = {'crawlers': tma_crawlers}
    return render(request, 'examiner/home.html', context)
