from typing import Optional

from django.db.models import F
from django.shortcuts import render

from examiner.models import PdfUrl


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

    context = {
        'exam_courses': exam_urls.organize(),
        'user': request.user,
    }
    if course_code:
        context['header_text'] = f' / exams / ' + course_code
    else:
        context['header_text'] = ' / exams'

    return render(request, 'examiner/exam_archive.html', context)
