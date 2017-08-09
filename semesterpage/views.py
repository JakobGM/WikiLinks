from gettext import gettext as _

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, mail_admins
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render

from dal import autocomplete
from subdomains.utils import reverse

from kokekunster.settings import ADMINS, SERVER_EMAIL
from dataporten.models import DataportenUser
from .adapters import (
    sync_dataporten_courses_with_db,
    sync_options_of_user_with_dataporten,
)
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
    if request.subdomain:
        # The user has visited xxx.example.com and is redirected to example.com/xxx,
        # the page for the study program or userpage xxx
        return redirect(reverse(
            viewname=study_program_view,
            subdomain=None, kwargs={'study_program': request.subdomain}
        ))
    else:
        # If the student has visited a student page before, redirect
        if request.session.get('homepage', ''):
            return redirect(reverse(
                'semesterpage-studyprogram',
                args=(request.session.get('homepage'),)
            ))

        semester_pk = request.session.get('semester_pk', DEFAULT_SEMESTER_PK)
        _semester = Semester.objects.get(pk=semester_pk)
        # Determine if it is a semester with a main profile or not, and redirect accordingly
        if _semester.main_profile:
            return redirect(reverse(
                'semesterpage-semester',
                args=[_semester.study_program.slug, _semester.main_profile.slug, _semester.number]
            ))
        else:
            return redirect(reverse(
                'semesterpage-simplesemester',
                args=[_semester.study_program.slug, _semester.number]
            ))


def study_program_view(request, study_program):
    if not StudyProgram.objects.filter(slug=study_program).exists():
        # This study program does not exist, thus we check if there is a studentpage
        # with the same name instead
        return studentpage(request, study_program)
    elif study_program == request.session.get('semester_slug', 'can not match this'):
        # The user has a saved location for this study program, and we can use it
        main_profile = request.session.get('main_profile_slug')
        semester_number = request.session.get('semester_number_slug')
        # Determine if it is a semester with a main profile or not, and redirect accordingly
        if main_profile:
            return redirect(reverse(
                'semesterpage-semester',
                args=[study_program, main_profile, semester_number]
            ))
        else:
            return redirect(reverse(
                'semesterpage-simplesemester',
                args=[study_program, semester_number]
            ))
    else:
        # Fall back on the lowest available semester (depends on the ordering of the semester model)
        default_semester = Semester.objects.filter(study_program__slug=study_program)[0]
        return redirect(default_semester.get_absolute_url())


def main_profile_view(request, study_program, main_profile):
    """
    Returns the semesterpage of the lowest available semester of the given main profile, or redirects the user to their
    last visited semester if that semester is part of the given main profile.
    """
    if (study_program == request.session.get('study_program_slug', 'no match')
        and main_profile == request.session.get('main_profile_slug', 'no match')):
        # The last visited semester is within this main profile, and we can therefore use the saved semester number
        return redirect(reverse(
            'semesterpage-semester',
            args=[
                study_program,
                main_profile,
                request.session.get('semester_number_slug')
            ]
        ))
    else:
        try:
            lowest_semester_number = Semester.objects.filter(
                study_program__slug=study_program,
                main_profile__slug=main_profile
            )[0].number
            return redirect(reverse(
                'semesterpage-semester',
                args=[study_program, main_profile, lowest_semester_number]
            ))
        except IndexError:
            raise Http404(_('Fant ingen semestre knyttet til hovedprofilen "%s" under studieprogrammet "%s".'
                            % (main_profile, study_program,)))


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

    if request.user.is_authenticated and isinstance(request.user, DataportenUser):
        # The user is authenticated through dataporten, and we use this opportunity
        # to update/create new course model objects from the dataporten data.
        dataporten_courses = request.user.dataporten.courses
        sync_dataporten_courses_with_db(courses=dataporten_courses.all)

        # And to add potentially new active courses to the student's
        # self_chosen_courses in order to make it more up to date.
        # And/or remove newly finished courses.
        sync_options_of_user_with_dataporten(user=request.user)
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
       }
    )


def simple_semester(request, study_program, semester_number):
    """
    A view for semesters that do not have a main profile related to it (simple semesters)
    """
    try:
        # Simple, unsplit semesters have NULL-value in the main_profile field, and there should be
        # max one for each semester number in a study program
        _semester = Semester.objects.get(study_program__slug=study_program, number=semester_number)

        if _semester.main_profile:
            # There is only one semester with the number 'semester_number', but it has a related
            # main profile, and therefore needs to be redirected to the URL that contains the main
            # profile slug
            return redirect(reverse(
                'semesterpage-semester',
                args=[_semester.study_program.slug, _semester.main_profile.slug, _semester.number]
            ))
        else:
            return semester(request, semester_object=_semester)

    except Semester.DoesNotExist:
        raise Http404(
            _('Felles %d. semester knyttet til studieprogrammet "%s" eksisterer ikke')
            % (int(semester_number), study_program))

    except Semester.MultipleObjectsReturned:
        # There are multiple semesters for this semester number, and we therefore redirect to the semesterpage
        # of the semester of the first main profile (according to MainProfile.Meta.ordering)
        _semester = Semester.objects.filter(study_program__slug=study_program, number=semester_number)[0]
        return redirect(reverse(
            'semesterpage-semester',
            args=[_semester.study_program.slug, _semester.main_profile.slug, _semester.number]
        ))


def semester(request, study_program=DEFAULT_STUDY_PROGRAM_SLUG, main_profile=None, semester_number='1', save_location=True, semester_object=None):
    """
    Generates the link portal for a given semester in a given program code
    """
    if semester_object is None:
        # (Premature?) optimization when semester query is already done in simple semester
        try:
            _semester = Semester.objects.get(study_program__slug=study_program, main_profile__slug=main_profile, number=int(semester_number))
        except Semester.DoesNotExist:
            raise Http404(
                _('%d. semester ved hovedprofilen "%s" knyttet til studieprogrammet "%s" eksisterer ikke')
                % (int(semester_number), main_profile, study_program)
            )
    else:
        _semester = semester_object

    if save_location:
        # Save the deliberate change of location by user in the session, as the semester has been found successfully
        request.session['semester_pk'] = _semester.pk
        request.session['study_program_slug'] = _semester.study_program.slug

        # Delete studentpage slug in order to prevent redirection to it
        request.session['homepage'] = ''

        if _semester.main_profile:
            request.session['main_profile_slug'] = _semester.main_profile.slug
        else:
            request.session['main_profile_slug'] = ''
        request.session['semester_number_slug'] = _semester.number
        request.session['homepage'] = ''  # Delete saved homepage

    # Where to send users if the semester has electives
    electives_url = ''
    if _semester.has_electives:
        if request.user.is_authenticated:
            electives_url = request.user.options.get_admin_url()
        else:
            electives_url = '/accounts/dataporten/login'

    return render(
        request,
        'semesterpage/courses.html',
        {
            'semester': _semester,
            'courses': _semester.courses.all(),
            'study_programs': StudyProgram.objects.filter(published=True),
            'calendar_name': get_calendar_name(request),
            'electives_url': electives_url,
            'user' : request.user,
        },
    )


def profile(request):
    """
    This view receives newly logged in users through django-allauth
    """
    return redirect(reverse('semesterpage-studyprogram', args=(request.user.username,)))


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


def simple_archive(request, study_program, semester_number):
    # This view is only needed in order to be able to reverse lookup arkiv.kokekunster.no/study_program/...
    # In order to do this, a url needed to be registered with a view name, but it is actually nginx that handles
    # the redirect to the arkiv.kokekunster.no domain where h5ai is used to index and portray the files in the webroot
    # TODO: These two views can be merged into one by using a conditional in urls.py and using main_profile=None
    # as a default argument
    return redirect(reverse(
        'semesterpage-simplearchive',
        subdomain='arkiv',
        args=[study_program.slug.title(), semester_number]
    ))


def split_archive(request, study_program, semester_number, main_profile):
    # This view is only needed in order to be able to reverse lookup arkiv.kokekunster.no/study_program/...
    # In order to do this, a url needed to be registered with a view name, but it is actually nginx that handles
    # the redirect to the arkiv.kokekunster.no domain where h5ai is used to index and portray the files in the webroot
    return redirect(reverse(
        'semesterpage-splitarchive',
        subdomain='arkiv',
        args=[study_program.slug.title(), semester_number.slug.title(), main_profile.slug.title()]
    ))


def calendar(request, calendar_name):
    """
    Saves the users choice of calendarname and then redirects
    """
    request.session['calendar_name'] = calendar_name
    if request.user.is_authenticated():
        request.user.options.calendar_name = calendar_name
        request.user.options.save()
    return redirect(to='https://ntnu.1024.no/' + calendar_name)


class CourseAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        """
        Returns a queryset used for autocompletion, restricted based
        on the user input.
        """
        # Only let logged in users access all the course information
        if not self.request.user.is_authenticated():
            return Course.objects.none()

        # Don't autocomplete courses which are already chosen
        already_chosen = Q(
            pk__in=self.request.user.options.self_chosen_courses.all(),
        )
        qs = Course.objects.exclude(already_chosen)

        # If the user has started entering input, start restricting
        # the choices available for autocompletion.
        if self.q:
            course_code = Q(course_code__istartswith=self.q)
            full_name = Q(full_name__istartswith=self.q)
            display_name = Q(display_name__startswith=self.q)
            qs = qs.filter(course_code | full_name | display_name)

        return qs
