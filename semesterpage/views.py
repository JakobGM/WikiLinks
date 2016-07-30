from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins, EmailMessage
from django.http import Http404
from subdomains.utils import reverse
from gettext import gettext as _
from collections import namedtuple, defaultdict
from .models import StudyProgram, Semester, ResourceLinkList
from .forms import LinkForm, FileForm
from kokekunster.settings import ADMINS, SERVER_EMAIL, DEFAULT_STUDY_PROGRAM


def getSemesterData(study_program, main_profile, semester_number):
    """
    Retrieve relevant data related to a given semester at a given study program
    """
    # Simple, unsplit semesters have NULL-value in the main_profile field,
    # but are given 'felles' as their main_profile url parameter
    main_profile_display_name = main_profile  # Used for Http404 response
    if main_profile == 'felles':
        main_profile = None

    SemesterData = namedtuple('SemesterData',
                              ['study_program',
                               'simple_semesters',
                               'grouped_split_semesters',
                               'semester',
                               'courses',
                               'resource_link_lists']
    )

    try:
        study_program = StudyProgram.objects.get(slug=study_program)
        semester = study_program.semesters.filter(main_profile__slug=main_profile).get(number=semester_number)
    except StudyProgram.DoesNotExist:
        raise Http404(_('Studieprogrammet "%s" eksisterer ikke') % study_program)
    except Semester.DoesNotExist:
        raise Http404(
            _(
                '%d. semester ved hovedprofilen "%s" '
                'knyttet til studieprogrammet "%s" eksisterer ikke'
            )
            % (semester_number, main_profile_display_name, study_program)
        )

    simple_semesters = study_program.semesters.filter(main_profile=None, published=True)
    split_semesters = study_program.semesters.exclude(main_profile=None).filter(published=True)

    courses = semester.courses.all()

    # Grouping the split semesters by semester.number
    grouped_split_semesters = defaultdict(list)
    for split_semester in split_semesters:
        grouped_split_semesters[split_semester.number].append(split_semester)

    # Get the ResourceLinkLists, falling back on the default ones if there are no custom ones for the study program
    if study_program.resource_link_lists.exists():
        resource_link_lists = study_program.resource_link_lists.all()
    else:
        resource_link_lists = ResourceLinkList.objects.filter(default=True)

    return SemesterData(
        study_program,
        simple_semesters,
        grouped_split_semesters.items(),
        semester,
        courses,
        resource_link_lists
    )


def homepage(request):
    """
    Homepage view for when the URL does not specify a specific semester.
    Looks at session data to see the user's last visited semester.
    If no data is given, the homepage defaults to the 1st semester
    of the study program given by DEFAULT_PROGRAM_CODE
    """
    if request.subdomain:
        # The user has visited xxx.example.com and is redirected to example.com/xxx, the page for the study program xxx
        return redirect(reverse(viewname=study_program_view, subdomain=None, kwargs={'study_program': request.subdomain}))
    else:
        study_program = request.session.get('study_program', DEFAULT_STUDY_PROGRAM)
        main_profile = request.session.get('main_profile', 'felles')
        semester_number = request.session.get('semester_number', '1')
        return semester(request, study_program, main_profile, semester_number, save_location=False)


def study_program_view(request, study_program):
    if not StudyProgram.objects.filter(slug=study_program).exists():
        # This study program does not exist, thus we check if there is a userpage
        # with the same name instead
        return userpage(request, study_program)
    elif study_program == request.session.get('study_program', 'no match'):
        # The user has a saved location for this study program, and we can use it
        main_profile = request.session.get('main_profile', 'felles')
        semester_number = request.session.get('semester_number', '1')
        return semester(request, study_program, main_profile, semester_number)
    elif not Semester.objects.filter(study_program__slug=study_program,
                                     main_profile=None,
                                     number=1
                                     ).exists():
        # The semester does not have a common 1st semester, so we have to fall back
        # on the lowest available semester (depends on the ordering of the semester
        # model)
        fall_back_semester = Semester.objects.filter(study_program__slug=study_program)[0]
        if fall_back_semester.main_profile is None:
            main_profile = 'felles'
        else:
            main_profile = fall_back_semester.main_profile.slug
        return semester(
            request=request,
            study_program=study_program,
            main_profile=main_profile,
            semester_number=fall_back_semester.number
        )
    else:
        # Using common first semester
        return semester(request, study_program)


def userpage(request, user):
    raise Http404('Userpage not implemented yet')


def semester(request, study_program=DEFAULT_STUDY_PROGRAM, main_profile='felles', semester_number='1', save_location=True):
    """
    Generates the link portal for a given semester in a given program code
    """
    # Query database for all the data required by the template
    semester_data = getSemesterData(study_program, main_profile, int(semester_number))

    if save_location:
        # Save the deliberate change of location by user in the session
        request.session['study_program'] = study_program
        request.session['main_profile'] = main_profile
        request.session['semester_number'] = semester_number

    # Boolean for changing the logo if the domain is fysmat.no
    is_fysmat = 'fysmat' in request.get_host().lower()

    return render(request, 'semesterpage/courses.html',
                  {'semester': semester_data.semester,
                   'courses': semester_data.courses,
                   'resource_link_lists': semester_data.resource_link_lists,
                   'simple_semesters': semester_data.simple_semesters,
                   'grouped_split_semesters': semester_data.grouped_split_semesters,
                   'study_programs': StudyProgram.objects.filter(published=True),
                   'is_fysmat': is_fysmat}
                  )


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
    semester_data = getSemesterData(program_code, semester_number)
    all_semesters = semester_data.all_semesters
    semester = semester_data.semester

    # Make sure to restrict course options to the courses related to the
    # semester which the user visited the request page from
    link_form.fields['course'].queryset = semester.courses
    file_form.fields['course'].queryset = semester.courses

    return render(request, 'semesterpage/user_request.html',
                  {'program_code': program_code,
                   'semesters': all_semesters,
                   'semester_number': semester_number,
                   'link_form': link_form,
                   'file_form': file_form}
                  )
