from random import randint
from typing import Optional

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.edit import FormView

from examiner.forms import VerifyExamForm
from examiner.models import ExamPdf, Pdf, PdfUrl
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

    context = {'exam_courses': exam_urls.organize()}
    add_context(request=request, context=context)
    if course_code:
        context['header_text'] = f' / exams / ' + course_code
        context['course'] = Course.objects.get(course_code=course_code.upper())
    else:
        context['header_text'] = ' / exams'

    return render(request, 'examiner/exam_archive.html', context)


class VerifyView(FormView, LoginRequiredMixin):
    template_name = 'examiner/verify.html'
    form_class = VerifyExamForm
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        """View for verifying PDF exam information."""
        sha1_hash = self.kwargs.get('sha1_hash')
        if sha1_hash:
            pdf = get_object_or_404(
                klass=Pdf,
                sha1_hash=sha1_hash,
            )
        else:
            exam_pdfs = ExamPdf.objects.filter(
                verified_by__isnull=True,
            )
            pdf = exam_pdfs[randint(0, exam_pdfs.count() - 1)].pdf

        exams = pdf.exams.all()
        form = VerifyExamForm(
            instance=pdf.exams.first(),
            initial={
                'courses': exams.values_list('course', flat=True),
                'pdf': pdf,
                'verifier': request.user,
            },
        )
        context = {'pdf': pdf, 'form': form}
        add_context(request, context)
        return render(request, 'examiner/verify.html', context)

    @transaction.atomic
    def form_valid(self, form):
        form.save(commit=True)
        return redirect(to='examiner:verify_random')


def add_context(request, context):
    """Add context required for navbar rendering."""
    semester_pk = request.session.get('semester_pk', DEFAULT_SEMESTER_PK)
    try:
        semester = Semester.objects.get(pk=semester_pk)
    except Semester.DoesNotExist:
        semester = None

    new_context = {
        'user': request.user,
        'study_programs': StudyProgram.objects.filter(published=True),
        'semester': semester,
    }
    context.update(new_context)
