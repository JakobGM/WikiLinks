import pytest

from .factories import (
        StudyProgramFactory,
        MainProfileFactory,
        SemesterFactory,
        CourseFactory,
        ResourceLinkListFactory,
        CourseLinkFactory,
        ResourceLinkFactory,
        ContributorFactory,
        OptionsFactory,
)


@pytest.fixture
def study_program():
    return StudyProgramFactory()

@pytest.fixture
def main_profile():
    return MainProfileFactory()

@pytest.fixture
def semester():
    return SemesterFactory()

@pytest.fixture
def course(semester):
    return CourseFactory(semesters=(semester,))

@pytest.fixture
def resource_link_list(study_program):
    return ResourceLinkListFactory(study_programs=(study_program,))

@pytest.fixture
def course_link():
    return CourseLinkFactory()

@pytest.fixture
def resource_link():
    return ResourceLinkFactory()

@pytest.fixture
def contributor():
    return ContributorFactory()

@pytest.fixture
def options():
    return OptionsFactory()
