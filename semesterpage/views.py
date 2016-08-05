from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins, EmailMessage
from django.http import Http404
from django.contrib.auth.models import User
from django.conf import settings
from subdomains.utils import reverse
from gettext import gettext as _
from .models import StudyProgram, Semester, Options
from .forms import LinkForm, FileForm
from kokekunster.settings import ADMINS, SERVER_EMAIL

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

    return render(request, 'semesterpage/userpage.html',
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


def calendar(request, calendar_name):
    """
    Saves the users choice of calendarname and then redirects
    """
    request.session['calendar_name'] = calendar_name
    if request.user.is_authenticated():
        request.user.options.calendar_name = calendar_name
        request.user.options.save()
    return redirect(to='https://ntnu.1024.no/' + calendar_name)


def sendLinkMail(request, link_form):
    """
    Sends an email to all addresses specified in kokekunster.settings.ADMINS.
    The content is the information submitted from the semesterapp.forms.LinkForm
    Assumption: link_form.is_valid() is True (pre-call validation)
    """
    cd = link_form.cleaned_data
    email_body = 'Title: ' + cd['title'] + \
                 '\nURL: ' + cd['url'] + \
                 '\nCourse: ' + str(cd['course']) + \
                 '\nCateogry: ' + str(cd['category']) + \
                 '\nDescription: ' + cd['description']
    mail_admins(
        'User link request from ' + str(request.get_host()),
        email_body
    )


def sendFileMail(request, file_form):
    """
    Sends an email to all addresses specified in kokekunster.settings.ADMINS.
    The content is the information submitted from the semesterapp.forms.FileForm
    Assumption: link_form.is_valid() is True (pre-call validation)
    """
    cd = file_form.cleaned_data
    email_body = 'Title: ' + cd['title'] + \
                 '\nCourse: ' + str(cd['course']) + \
                 '\nDescription: ' + cd['description']
    email = EmailMessage(
        subject='Link request from ' + str(request.get_host()),
        body=email_body,
        from_email=SERVER_EMAIL,
        to=ADMINS
    )

    user_files = request.FILES['user_files']
    for uf in request.FILES.getlist('user_files'):
        if uf.content_type == 'text/plain':
            # A VERY hacky solution until this mime type attachment bug is solved
            file_content = str(uf.read())
            # file_content.encode(uf.encoding)

            email.body += '\n\n===ATTACHED FILE text/plain===' + \
                          '\nFilename: ' + uf.name + \
                          '\n\n===Raw file content===\n' + \
                          file_content
        else:
            email.attach(uf.name, uf.read(), uf.content_type)

    email.send()


def user_request(request, program_code, semester_number):
    """
    Portrays two forms, one for uploading files and another one for sending
    link requests. Sends an email to the admin email address
    TODO: Handle these requests with a "admin accept proposal" feature and
    then automatic inclusion in the database
    """
    # If one of the forms have been submitted, process it
    if request.method == 'POST':
        print('metode: post')
        request_type = request.POST['request_type']
        # Branch after determination of which form that has been submitted
        if request_type == 'link':
            link_form = LinkForm(request.POST)
            file_form = FileForm()
            if link_form.is_valid():
                sendLinkMail(request, link_form)
        elif request_type == 'file':
            file_form = FileForm(request.POST, request.FILES)
            link_form = LinkForm()
            if file_form.is_valid():
                sendFileMail(request, file_form)
        else:
            # Should never reach this statement as there are only two forms
            # which call this view
            raise ValidationError(_('Skjematype er verken av type \"lenke\" eller \"fil\"'))
    else:
        # The form has not been submitted, so both forms have to be initialized to
        # their unbound state
        link_form, file_form = LinkForm(), FileForm()

    # Render the template with context from the above else-if evaluation
    # semester_data = getSemesterData(program_code, semester_number)
    # all_semesters = semester_data.all_semesters
    # semester = semester_data.semester
    #
    # # Make sure to restrict course options to the courses related to the
    # # semester which the user visited the request page from
    # link_form.fields['course'].queryset = semester.courses
    # file_form.fields['course'].queryset = semester.courses
    #
    # return render(request, 'semesterpage/user_request.html',
    #               {'program_code': program_code,
    #                'semesters': all_semesters,
    #                'semester_number': semester_number,
    #                'link_form': link_form,
    #                'file_form': file_form}
    #               )
