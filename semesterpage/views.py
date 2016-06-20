from django.shortcuts import render
from collections import namedtuple
from .models import StudyProgram, Semester, Course
from .forms import LinkForm, FileForm


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


def semester(request, program_code, semester_number):
    """
    Generates the link portal for a given semester in a given program code
    """
    study_program, all_semesters, semester, courses = getSemesterData(program_code, semester_number)

    # Boolean for changing the logo if the domain is fysmat.xxx
    is_fysmat = 'fysmat' in request.get_host().lower()

    return render(request, 'semesterpage/courses.html',
                  {'semester_number': semester.number,
                   'courses': courses,
                   'semesters': all_semesters,
                   'is_fysmat': is_fysmat}
                  )


def user_request(request, program_code, semester_number):
    """
    Portrays two forms, one for uploading files and another one for sending
    link requests. Sends an email to the admin email address 
    TODO: Handle these requests with a "admin accept proposal" feature and
    then automatic inclusion in the database
    """
    semester_data = getSemesterData(program_code, semester_number)
    all_semesters = semester_data.all_semesters
    semester = semester_data.semester

    # Create link and file form, where the user can select from the courses
    # which are part of the semesterpage which (s)he came from
    link_form, file_form = LinkForm(), FileForm()
    link_form.fields['course'].queryset = semester.courses
    file_form.fields['course'].queryset = semester.courses

    return render(request, 'semesterpage/user_request.html',
                  {'program_code': program_code,
                   'semesters': all_semesters,
                   'semester_number': semester_number,
                   'link_form': link_form,
                   'file_form': file_form}
                  )
