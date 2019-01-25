from random import randint

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from examiner.forms import ExamsSearchForm, VerifyExamForm
from examiner.models import DocumentInfo, DocumentInfoSource, Pdf, PdfUrl
from semesterpage.models import Course, Semester, StudyProgram
from semesterpage.views import CourseAutocomplete


DEFAULT_SEMESTER_PK = getattr(settings, 'DEFAULT_SEMESTER_PK', 1)


class ExamsView(ListView):
    model = PdfUrl
    template_name = 'examiner/exam_archive.html'
    http_method_names = ['get']

    def get_context_data(self, **kwargs):
        super().get_context_data(**kwargs)
        course_code = self.kwargs.get('course_code')
        docinfos = (
            DocumentInfo
            .objects
            .order_by(
                F('course_code'),
                F('year').desc(nulls_last=True),
                F('solutions').desc(),
            )
        )
        if course_code:
            docinfos = docinfos.filter(
                course_code__iexact=course_code.upper(),
            )

        context = {'exam_courses': docinfos.organize()}

        if self.kwargs.get('api'):
            # Early return if this is the API view
            return context['exam_courses']

        add_context(request=self.request, context=context)
        if course_code:
            context['header_text'] = f' / exams / ' + course_code
            context['course'] = Course.objects.get(
                course_code=course_code.upper(),
            )
        else:
            context['header_text'] = ' / exams'

        return context

    def get(self, request, *args, **kwargs):
        if self.kwargs.get('api'):
            # Hacky override for API version of this view
            self.object_list = self.get_queryset()
            organization = self.get_context_data()
            return JsonResponse(organization)

        # Normal template response
        return super().get(request, *args, **kwargs)


class VerifyView(LoginRequiredMixin, FormView):
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
            exam_pdfs = DocumentInfoSource.objects.filter(
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


class CourseWithExamsAutocomplete(CourseAutocomplete):
    """Autocompletion view for courses with related exams."""

    LOGIN_REQUIRED = False

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(docinfos__isnull=False).distinct()


class SearchView(FormView):
    """View for course search."""

    template_name = 'examiner/search.html'
    form_class = ExamsSearchForm
    http_method_names = ['get', 'post']

    def form_valid(self, form):
        """Redirect to exam archive for course."""
        # Get the first element, because we use a multiple choice field for
        # aesthetic reasons.
        course = form.cleaned_data['course'][0]
        return redirect(
            to='examiner:course',
            course_code=course.course_code,
        )

    def get_context_data(self, **kwargs):
        """Add navigation bar content."""
        context = super().get_context_data(**kwargs)
        add_context(request=self.request, context=context)
        return context


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
