from gettext import gettext as _

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, mail_admins
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpRequest
from django.shortcuts import redirect, render, reverse as django_reverse
from django.urls import resolve

from dal import autocomplete
from rules.contrib.views import permission_required, objectgetter
from subdomains.utils import reverse

from kokekunster.settings import ADMINS, SERVER_EMAIL
from dataporten.models import DataportenUser
from .adapters import reconcile_dataporten_data
from .admin import CourseAdmin
from .models import Course, Options, Semester, StudyProgram

DEFAULT_STUDY_PROGRAM_SLUG = getattr(settings, 'DEFAULT_STUDY_PROGRAM_SLUG', 'fysmat')
DEFAULT_SEMESTER_PK = getattr(settings, 'DEFAULT_SEMESTER_PK', 1)

def homepage(request):
    """
    Homepage view for when the URL does not specify a specific semester.
    Looks at session data to see the user's last visited semester.
    If no data is given, the homepage defaults to the semester
    given by DEFAULT_SEMESTER_PK
    """
    if request.user.is_authenticated:
        return redirect(to=request.user.options.get_absolute_url())
    elif request.session.get('homepage', ''):
        # If the student has visited a student page before, redirect
        return redirect(django_reverse(
            'semesterpage-studyprogram',
            args=(request.session.get('homepage'),)
        ))
    else:
        semester_pk = request.session.get('semester_pk', DEFAULT_SEMESTER_PK)
        semester = Semester.objects.get(pk=semester_pk)
        return redirect(to=semester.get_absolute_url())

def studentpage(request, homepage):
    # NB! In the following view function, user and request.user is not necessarily
    # the same user. This should become more clear in the next refactoring
    try:
        # The homepage is given by the (Feide) username
        user = User.objects\
                .select_related('options', 'contributor')\
                .prefetch_related('options__self_chosen_courses__links')\
                .get(username=homepage)

    except User.DoesNotExist:
        raise Http404(_('Fant ingen studieprogram eller brukerside med navnet "%s"') % homepage)

    if request.user.is_authenticated \
            and isinstance(request.user, DataportenUser) \
            and request.user.username == homepage:
        # We ensure normalization between dataporten and the database,
        # since we have an authenticated dataporten user which tries to acces
        # his/her own homepage.
        reconcile_dataporten_data(request.user)
        user.refresh_from_db()

    # Save homepage in session for automatic redirect on next visit
    request.session['homepage'] = homepage

    return render(request, 'semesterpage/userpage-courses.html', {
           'semester': user.options,
           'courses': user.options.courses,
           'study_programs': StudyProgram.objects.filter(published=True),
           'calendar_name': get_calendar_name(request),
           'user': request.user,
           'header_text': f' / {user.username}',
           'student_page': True,
       }
    )


def semester_view(request, study_program, main_profile=None, semester_number=None, save_location=True):
    """
    Generates the link portal for a given semester in a given program code
    """
    try:
        semester = Semester.get(study_program, main_profile, semester_number)
    except Semester.DoesNotExist:
        if not main_profile and not semester_number:
            # This URL might refer to a userpage instead
            return studentpage(request, study_program)
        raise Http404(
            _('%s. semester ved hovedprofilen "%s" knyttet til studieprogrammet "%s" eksisterer ikke')
            % ((semester_number or 'Et'), main_profile or 'felles', study_program)
        )

    if save_location:
        # Save the deliberate change of location by user in the session, as the semester has been found successfully
        request.session['semester_pk'] = semester.pk
        request.session['study_program_slug'] = semester.study_program.slug

        # Delete studentpage slug in order to prevent redirection to it
        request.session['homepage'] = ''

        if semester.main_profile:
            request.session['main_profile_slug'] = semester.main_profile.slug
        else:
            request.session['main_profile_slug'] = ''
        request.session['semester_number_slug'] = semester.number
        request.session['homepage'] = ''  # Delete saved homepage

    # Where to send users if the semester has electives
    electives_url = ''
    if semester.has_electives:
        if request.user.is_authenticated:
            electives_url = request.user.options.get_admin_url()
        else:
            electives_url = '/accounts/dataporten/login'

    return render(
        request,
        'semesterpage/courses.html',
        {
            'semester': semester,
            'courses': semester.courses.all(),
            'study_programs': StudyProgram.objects.filter(published=True),
            'calendar_name': get_calendar_name(request),
            'electives_url': electives_url,
            'user': request.user,
            'student_page': False,
        },
    )


@login_required
def profile(request):
    """
    This view receives newly logged in users through django-allauth. It
    redirects to the options admin url if the student has not selected their
    active courses, and redirects to their student page elsewise.
    """
    if settings.PICK_COURSES_ON_FIRST_LOGIN and \
            not request.user.options.last_user_modification:
        return redirect(request.user.options.get_admin_url())
    else:
        return redirect(django_reverse(
            'semesterpage-studyprogram',
            args=(request.user.username,)
        ))


def get_calendar_name(request):
    """
    # Checks if the user has a saved calendar name and returns it
    """
    # TODO: Try-except should be replaced
    try:
        if request.user.options.calendar_name:
            # Saved in options
            return request.user.options.calendar_name
    except AttributeError:
        pass
    # Saved in session
    return request.session.get('calendar_name', None)

def calendar(request, calendar_name):
    """
    Saves the users choice of calendarname and then redirects
    """
    request.session['calendar_name'] = calendar_name
    if request.user.is_authenticated():
        request.user.options.calendar_name = calendar_name
        request.user.options.save()
    return redirect(to='https://ntnu.1024.no/' + calendar_name)

def admin_login(request: HttpRequest) -> HttpResponse:
    """
    The admin site login is wrapped in the login_required decorator. This way
    we can link directly to admin pages, and non-authenticated users will be
    sent to settings.LOGIN_URL with an appropiate ?next=... parameter instead.
    Unfortunately, the django admin does not respect the query redirect
    parameter, so this view intercepts the view logic and redirects if the user
    has returned from a successful login.
    """
    if request.user.is_authenticated and 'next' in request.GET:
        # The user has returned from the login provider
        return redirect(request.GET['next'])
    else:
        # The user has not yet performed the login
        return admin.site.login(request)

def admin_course_history(request: HttpRequest, course_pk: str) -> HttpResponse:
    """
    Only allows superusers to view the history of a Course model object in the
    admin.
    """
    if request.user.is_superuser:
        # Hacky way to access the history_view of CourseAdmin, as I have not
        # found any other way to retrieve it. This is partly caused by this
        # view being the resolver of 'admin:semesterpage_course_history'.
        return admin.site._registry[Course].history_view(request, course_pk)
    else:
        # Don't need to do anything overly clever here, as this is not a normal
        # use case at all.
        return redirect('/')

@permission_required(
    'semesterpage.change_course',
    fn=objectgetter(Course, 'course_pk'),
)
def new_course_url(request, course_pk: str) -> HttpResponse:
    """
    A user has specified a URL for a course which previously had none.
    This should be saved to the Course model object before redirecting
    to the course homepage.
    """
    homepage_url = request.GET.get('homepage_url', '')

    # Need to prevent relative links
    if not homepage_url[:4].lower() == 'http':
        homepage_url = 'http://' + homepage_url

    course = Course.objects.get(pk=int(course_pk))
    course.homepage = homepage_url.strip()
    course.save(update_fields=['homepage'])
    return redirect(course.homepage)


@login_required
def remove_course(request, course_pk: str) -> HttpResponse:
    """
    A user wishes to hide a course from their course page, and shall be
    returned to the student page after it has been hidden.
    """
    request.user.options.self_chosen_courses.remove(course_pk)
    return redirect(to=request.user.options.get_absolute_url())


class CourseAutocomplete(autocomplete.Select2QuerySetView):
    LOGIN_REQUIRED = False

    def get_queryset(self):
        """
        Returns a queryset used for autocompletion, restricted based
        on the user input.
        """
        # Only let logged in users access all the course information
        if self.LOGIN_REQUIRED and not self.request.user.is_authenticated():
            return Course.objects.none()

        qs = Course.objects.all()

        # If the user has started entering input, start restricting
        # the choices available for autocompletion.
        if self.q:
            course_code = Q(course_code__istartswith=self.q)
            full_name = Q(full_name__istartswith=self.q)
            display_name = Q(display_name__istartswith=self.q)
            qs = qs.filter(course_code | full_name | display_name)

        return qs
