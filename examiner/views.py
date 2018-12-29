from typing import Optional

from django.conf import settings
from django.db.models import F
from django.shortcuts import render

from examiner.models import PdfUrl
from semesterpage.models import Course, Semester, StudyProgram


DEFAULT_SEMESTER_PK = getattr(settings, 'DEFAULT_SEMESTER_PK', 1)


def exams(request, course_code: Optional[str] = None):
    exam_urls = (
        PdfUrl
        .objects
        .order_by(
            F('exam__course_code'),
            F('exam__year').desc(nulls_last=True),
            F('exam__solutions').desc(),
        )
    )
    if course_code:
        exam_urls = exam_urls.filter(
            exam__course_code__iexact=course_code.upper(),
        )

    semester_pk = request.session.get('semester_pk', DEFAULT_SEMESTER_PK)
    try:
        semester = Semester.objects.get(pk=semester_pk)
    except Semester.DoesNotExist:
        semester = None

    context = {
        'exam_courses': exam_urls.organize(),
        'user': request.user,
        'study_programs': StudyProgram.objects.filter(published=True),
        'semester': semester,
    }
    if course_code:
        context['header_text'] = f' / exams / ' + course_code
        context['course'] = Course.objects.get(course_code=course_code.upper())
    else:
        context['header_text'] = ' / exams'

    return render(request, 'examiner/exam_archive.html', context)
