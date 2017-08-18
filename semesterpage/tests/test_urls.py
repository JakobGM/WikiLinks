from django.test import TestCase
from django.urls import resolve, reverse

from .factories import (
    CourseFactory,
    MainProfileFactory,
    OptionsFactory,
    SemesterFactory,
    StudyProgramFactory,
)


def test_simple_semester():
    simple_url = reverse(
        'semesterpage-simplesemester',
        args=['fysmat', '1'],
    )
    assert simple_url == '/fysmat/1/'

    resolver = resolve('/fysmat/1/')
    assert resolver.view_name == 'semesterpage-simplesemester'
    assert resolver.func.__name__ == 'simple_semester'

    kwargs = {
        'study_program': 'fysmat',
        'semester_number': '1',
    }
    assert resolver.kwargs == kwargs

    simple_semester = SemesterFactory.build(
        main_profile=None,
        study_program__slug='fysmat',
    )
    assert simple_semester.get_absolute_url() == '/fysmat/1/'

def test_study_program():
    study_program_url = reverse(
        'semesterpage-studyprogram',
        args=['fysmat'],
    )
    assert study_program_url == '/fysmat/'

    resolver = resolve('/fysmat/')
    assert resolver.view_name == 'semesterpage-studyprogram'
    assert resolver.func.__name__ == 'study_program_view'

    kwargs = {
        'study_program': 'fysmat',
    }
    assert resolver.kwargs == kwargs

    study_program = StudyProgramFactory.build(
        slug='fysmat',
    )
    assert study_program.get_absolute_url() == '/fysmat/'

def test_main_profile():
    main_profile_url = reverse(
        'semesterpage-mainprofile',
        args=['fysmat', 'inmat'],
    )
    assert main_profile_url == '/fysmat/inmat/'

    resolver = resolve('/fysmat/inmat/')
    assert resolver.view_name == 'semesterpage-mainprofile'
    assert resolver.func.__name__ == 'main_profile_view'

    kwargs = {
        'study_program': 'fysmat',
        'main_profile': 'inmat',
    }
    assert resolver.kwargs == kwargs

    main_profile = MainProfileFactory.build(
        slug='inmat',
        study_program__slug='fysmat',
    )
    assert main_profile.get_absolute_url() == '/fysmat/inmat/'

def test_semester():
    semester_url = reverse(
        'semesterpage-semester',
        args=['fysmat', 'inmat', '1'],
    )
    assert semester_url == '/fysmat/inmat/1/'

    resolver = resolve('/fysmat/inmat/1/')
    assert resolver.view_name == 'semesterpage-semester'
    assert resolver.func.__name__ == 'semester'

    kwargs = {
        'study_program': 'fysmat',
        'main_profile': 'inmat',
        'semester_number': '1',
    }
    assert resolver.kwargs == kwargs

    semester = SemesterFactory.build(
        number=1,
        main_profile__slug='inmat',
        study_program__slug='fysmat',
    )
    assert semester.get_absolute_url() == '/fysmat/inmat/1/'

def test_studentpage():
    options_url = reverse(
        'semesterpage-studyprogram',
        args=['olan'],
    )
    assert options_url == '/olan/'

    resolver = resolve('/olan/')
    assert resolver.view_name == 'semesterpage-studyprogram'
    assert resolver.func.__name__ == 'study_program_view'

    kwargs = {
        'study_program': 'olan'
    }
    assert resolver.kwargs == kwargs

    options = OptionsFactory.build(
        user__username='olan',
    )
    assert options.get_absolute_url() == '/olan/'

def test_course_history():
    history_url = reverse(
        'semesterpage-course-history',
        args=['1'],
    )
    assert history_url == '/oppdater/semesterpage/course/1/history/'

    resolver = resolve('/oppdater/semesterpage/course/1/history/')
    assert resolver.view_name == 'semesterpage-course-history'
    assert resolver.func.__name__ == 'admin_course_history'
    assert resolver.args == ('1',)
