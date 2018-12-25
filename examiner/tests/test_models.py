from pathlib import Path

from django.core.files.base import ContentFile
from django.db.utils import IntegrityError

import pytest

import responses

from examiner.models import Exam, Pdf, PdfUrl
from examiner.parsers import Language, Season
from dataporten.tests.factories import UserFactory
from semesterpage.tests.factories import CourseFactory


@pytest.mark.django_db
def test_derive_course_from_course_code_on_save():
    """Exam model objects should connect course code and course on save."""
    course = CourseFactory(course_code='TMA4130')
    exam = Exam.objects.create(course_code='TMA4130')
    assert exam.course == course

    url = 'http://www.example.com/TMA4130/2013h/oldExams/eksamen-bok_2006v.pdf'
    exam_url = PdfUrl(url=url)
    exam_url.parse()
    assert exam_url.exam.course == course


@pytest.mark.django_db
def test_derive_course_code_from_course_on_save():
    """The course code should be derived from the course foreign key."""
    course = CourseFactory(course_code='TMA4130')
    exam = Exam.objects.create(course=course)
    assert exam.course_code == 'TMA4130'


@pytest.mark.django_db
def test_prevention_of_non_unique_url():
    """URLs should be unique."""
    url = 'http://www.example.com/TMA4130/2013h/oldExams/eksamen-bok_2006v.pdf'
    exam_url1 = PdfUrl(url=url)
    exam_url1.save()

    exam_url2 = PdfUrl(url=url)
    with pytest.raises(IntegrityError):
        exam_url2.save()


@pytest.mark.django_db
def test_parse_url():
    """The parse_url method should update model fields from url parsing."""
    url = 'http://www.example.com/TMA4130/2013h/oldExams/eksamen-bok_2006v.pdf'
    exam_url = PdfUrl(url=url)
    exam_url.parse()
    exam_url.save()
    assert exam_url.url == url

    # At first, the course does not exist, so only the string is saved
    assert exam_url.exam.course is None
    assert exam_url.exam.course_code == 'TMA4130'

    # All other fields have been inferred
    assert exam_url.filename == 'eksamen-bok_2006v.pdf'
    assert exam_url.probably_exam is True

    assert exam_url.exam.language == Language.BOKMAL
    assert exam_url.exam.year == 2006
    assert exam_url.exam.season == Season.SPRING
    assert exam_url.exam.solutions is False
    assert exam_url.verified_by.count() == 0
    assert exam_url.created_at
    assert exam_url.updated_at

    # Now we create the course and resave the exam model object
    course = CourseFactory(course_code='TMA4130')
    course.save()
    exam_url.exam.save()

    # The course should now be properly set
    assert exam_url.exam.course == course


@pytest.mark.django_db
def test_parse_url_of_already_verified_url():
    """Parsing a verified url should not mutate the object."""
    url = 'http://www.example.com/TMA4130/2013h/oldExams/eksamen-bok_2006v.pdf'
    exam_url = PdfUrl(url=url)

    # First, the parser infers 2006 as the year
    exam_url.parse()
    exam_url.save()
    assert exam_url.exam.year == 2006

    # Then the exam year is modified by a user
    exam_url.exam = Exam.objects.create(year=2016)
    exam_url.save()

    # And thereafter verified by that user
    user = UserFactory(username='verifier')
    user.save()
    exam_url.verified_by.add(user)

    # On reparsing the url, attributes are not changed
    exam_url.parse()
    assert exam_url.exam.year == 2016


@responses.activate
@pytest.mark.django_db
def test_file_backup(tmpdir, settings):
    # Create a trivial exam file
    tmpdir = Path(tmpdir)
    test_file = tmpdir / 'tmp_exam.txt'
    test_file.touch()
    test_file.write_text('Exam text')

    # This file is "hosted" at this URL
    url = 'http://www.example.com/TMA4130/2013h/oldExams/eksamen.txt'

    # Mock the file download from this URL
    responses.add(
        responses.GET,
        url,
        body=test_file.read_bytes(),
        status=200,
        content_type='text/plain',
        stream=True,
    )

    # We now backup this file
    exam_url = PdfUrl(url=url)
    exam_url.backup_file()
    exam_url.refresh_from_db()

    # The downloaded file should be hashed and the result stored
    assert exam_url.dead_link is False
    expected_sha1_hash = '4dc828ea76ab618be6d72d135af13c40de3b9ce6'
    file_backup = exam_url.scraped_pdf
    assert file_backup.sha1_hash == expected_sha1_hash

    # And the stored file should be named according to its hash
    assert file_backup.file.name == 'examiner/FileBackup/' + expected_sha1_hash

    # The directory for file backups should now contain one file
    backup_directory = Path(settings.MEDIA_ROOT / 'examiner/FileBackup/')
    assert len(list(backup_directory.iterdir())) == 1

    # Now we take a look at a new url
    new_url = 'http://example.com/ny_eksamen.txt'

    # But this url returns the same file as previous
    responses.add(
        responses.GET,
        new_url,
        body=test_file.read_bytes(),
        status=200,
        content_type='text/plain',
        stream=True,
    )
    new_exam_url = PdfUrl(url=new_url)
    new_exam_url.backup_file()
    assert len(list(backup_directory.iterdir())) == 1
    assert PdfUrl.objects.all().count() == 2
    assert Pdf.objects.all().count() == 1
    assert exam_url.scraped_pdf == new_exam_url.scraped_pdf


@responses.activate
@pytest.mark.django_db
def test_file_backup_of_dead_link(tmpdir, settings):
    """A dead URL should be handled properly."""
    # This file was "hosted" at this URL
    url = 'http://www.example.com/TMA4130/2013h/oldExams/dead_link.txt'

    # But the URL now returns 404
    responses.add(
        responses.GET,
        url,
        body=b"404",
        status=404,
        content_type='text/plain',
        stream=True,
    )

    # We scrape this URL
    exam_url = PdfUrl(url=url)
    exam_url.parse()
    assert exam_url.dead_link is None

    # And then unsucessfully try to backup the file
    exam_url.backup_file()
    exam_url.refresh_from_db()
    assert exam_url.dead_link is True


@pytest.mark.django_db
def test_queryset_organize_method():
    """ExamURLs should be organizable in hierarchy."""
    exam1 = Exam.objects.create(
        course_code='TMA4000',
        year=2016,
        season=Season.SPRING,
        language=Language.ENGLISH,
    )
    exam_url1 = PdfUrl.objects.create(
        url='http://exams.com/exam',
        exam=exam1,
    )

    exam1_solutions = Exam.objects.create(
        course_code='TMA4000',
        year=2016,
        season=Season.SPRING,
        solutions=True,
        language=Language.ENGLISH,
    )
    exam_url_solutions = PdfUrl.objects.create(
        url='http://exams.com/solution',
        exam=exam1_solutions
    )

    eksamen_losning = Exam.objects.create(
        course_code='TMA4000',
        year=2016,
        season=Season.SPRING,
        solutions=True,
        language=Language.BOKMAL,
    )
    eksamen_url_losning = PdfUrl.objects.create(
        url='http://exams.com/losning',
        exam=eksamen_losning,
    )

    CourseFactory(
        full_name='Mathematics 1',
        display_name='Maths 1',
        course_code='TMA4000',
    )
    organization = PdfUrl.objects.all().organize()
    assert organization == {
        'TMA4000': {
            'full_name': 'Mathematics 1',
            'nick_name': 'Maths 1',
            'years': {
                2016: {
                    'Vår': {
                        'exams': {'Engelsk': [exam_url1]},
                        'solutions': {
                            'Bokmål': [eksamen_url_losning],
                            'Engelsk': [exam_url_solutions],
                        },
                    },
                },
            },
        },
    }


@pytest.mark.django_db
def test_string_content():
    """FileBackup PDFs should be parsable."""
    pdf_path = Path(__file__).parent / 'data' / 'matmod_exam_des_2017.pdf'
    pdf_content = ContentFile(pdf_path.read_bytes())
    sha1 = 'a8c5b61d8e750db6e719937a251e93b9'
    pdf_backup = Pdf(sha1_hash=sha1)
    pdf_backup.file.save(sha1, content=pdf_content)
    pdf_backup.read_text()
    pdf_backup.save()

    pdf_backup.refresh_from_db()

    # Ensure unicode string
    assert isinstance(pdf_backup.text, str)

    # Check content with text property
    assert len(pdf_backup.text.split('\f')) == 6
    assert 'Rottman' in pdf_backup.text
    assert 'population model' in pdf_backup.text
    assert 'this is not in the exam' not in pdf_backup.text

    # Check associated PdfPage model objects
    pages = pdf_backup.pages.all()
    assert pages.count() == 6

    # The ordering should be based on page number
    for page_num, page in enumerate(pages):
        assert page.number == page_num
        assert page.confidence is None

    # And each page should containt content
    assert 'Rottman' in pages[0].text
    assert 'Rottman' not in pages[2].text

    assert 'population model' in pages[2].text
    assert 'population model' not in pages[0].text


@responses.activate
@pytest.mark.django_db
def test_deletion_of_file_on_delete(tmpdir, settings):
    """FileField file should be cleaned up on Pdf deletion."""
    # Create Pdf object with associated downloaded file
    sha1_hash = '4dc828ea76ab618be6d72d135af13c40de3b9ce6'
    pdf = Pdf(sha1_hash=sha1_hash)
    pdf.file.save(content=ContentFile('Exam text'), name=sha1_hash, save=True)

    # The file should now exist on disk
    filepath = Path(settings.MEDIA_ROOT, pdf.file.name)
    assert filepath.is_file()

    # But after deleting the model, the file should be cleaned as well
    pdf.delete()
    assert not filepath.is_file()
