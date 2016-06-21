from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins, send_mail, EmailMessage
from gettext import gettext as _
from collections import namedtuple
from .models import StudyProgram, Semester, Course
from .forms import LinkForm, FileForm
from kokekunster.settings import ADMINS, SERVER_EMAIL


def getSemesterData(program_code, semester_number):
    """
    Retrieve relevant data related to a given semester at a given study program
    TODO: Add compatibility for semesters with several main profiles
    """
    SemesterData = namedtuple('SemesterData',
                              ['study_program',
                               'all_semesters',
                               'semester',
                               'courses']
                              )
    study_program = StudyProgram.objects.get(program_code__iexact=program_code)
    all_semesters = study_program.semesters.all()
    semester = all_semesters.get(number=semester_number)
    courses = semester.courses.all()
    return SemesterData(study_program, all_semesters, semester, courses)


def semester(request, program_code, semester_number='1'):
    """
    Generates the link portal for a given semester in a given program code
    """
    study_program, all_semesters, semester, courses = getSemesterData(program_code, int(semester_number))

    # Boolean for changing the logo if the domain is fysmat.xxx
    is_fysmat = 'fysmat' in request.get_host().lower()

    return render(request, 'semesterpage/courses.html',
                  {'semester_number': semester.number,
                   'courses': courses,
                   'semesters': all_semesters,
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
