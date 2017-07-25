from gettext import gettext as _

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, mail_admins
from django.http import Http404
from django.shortcuts import redirect, render
from subdomains.utils import reverse

from kokekunster.settings import ADMINS, SERVER_EMAIL

from .forms import FileForm, LinkForm
from .models import Options, Semester, StudyProgram

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
    try:
        options = Options.objects.get(homepage_slug=homepage)
    except Options.DoesNotExist:
        raise Http404(_('Fant ingen studieprogram eller brukerside med navnet "%s"') % homepage)

    # Boolean for changing the logo if the domain is fysmat.no
    is_fysmat = 'fysmat' in request.get_host().lower()

    return render(request, 'semesterpage/userpage-courses.html',
                  {'semester': options,
                   'study_programs': StudyProgram.objects.filter(published=True),
                   'calendar_name': get_calendar_name(request),
                   'is_fysmat': is_fysmat,
                   'user': request.user}
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
        if _semester.main_profile:
            request.session['main_profile_slug'] = _semester.main_profile.slug
        else:
            request.session['main_profile_slug'] = ''
        request.session['semester_number_slug'] = _semester.number
        request.session['homepage'] = ''  # Delete saved homepage

    # Boolean for changing the logo if the domain is fysmat.no
    is_fysmat = 'fysmat' in request.get_host().lower()

    return render(request, 'semesterpage/courses.html',
                  {'semester': _semester,
                   'study_programs': StudyProgram.objects.filter(published=True),
                    'calendar_name': get_calendar_name(request),
                   'is_fysmat': is_fysmat,
                   'user' : request.user}
                  )


def profile(request):
    options = request.user.options
    if options.self_chosen_semester is None and not options.self_chosen_courses.exists() or not options.homepage_slug:
        return redirect(reverse('admin:semesterpage_options_change', args=(options.id,)))
    else:
        return redirect(reverse('semesterpage-studyprogram', args=(request.user.options.homepage_slug,)))


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
