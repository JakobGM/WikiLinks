from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError

import pytest

import responses

from examiner.models import (
    Exam,
    ExamPdf,
    ExamRelatedCourse,
    Pdf,
    PdfPage,
    PdfUrl,
)
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
    exam_url.classify()
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
def test_url_classify_method():
    """The classify method should update model fields from url parsing."""
    url = 'http://www.example.com/TMA4130/2013h/oldExams/eksamen-bok_2006v.pdf'
    exam_url = PdfUrl(url=url)
    exam_url.classify()
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
def test_classify_url_of_already_verified_url():
    """Parsing a verified url should not mutate the object."""
    url = 'http://www.example.com/TMA4130/2013h/oldExams/eksamen-bok_2006v.pdf'
    exam_url = PdfUrl(url=url)

    # First, the parser infers 2006 as the year
    exam_url.classify()
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
    exam_url.classify()
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
    assert (
        file_backup.file.name ==
        'examiner/FileBackup/' + expected_sha1_hash + '.pdf'
    )

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
    exam_url.classify()
    assert exam_url.dead_link is None

    # And then unsucessfully try to backup the file
    exam_url.backup_file()
    exam_url.refresh_from_db()
    assert exam_url.dead_link is True


@pytest.mark.django_db
def test_queryset_organize_method():
    """ExamURLs should be organizable in hierarchy."""
    # All links are related to this course
    CourseFactory(
        full_name='Mathematics 1',
        display_name='Maths 1',
        course_code='TMA4000',
    )

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

    # The URL classifier could not determine the language
    url_exam_2015 = Exam.objects.create(
        course_code='TMA4000',
        year=2015,
        season=Season.SPRING,
        solutions=False,
        language=Language.UNKNOWN,
    )

    # But the PDF classifier managed to determine it
    pdf_exam_2015 = Exam.objects.create(
        course_code='TMA4000',
        year=2015,
        season=Season.SPRING,
        solutions=False,
        language=Language.ENGLISH,
    )
    exam_2015_pdf = Pdf.objects.create()
    ExamPdf.objects.create(
        exam=pdf_exam_2015,
        pdf=exam_2015_pdf,
    )

    # The pdf is scraped
    exam_2015_url = PdfUrl.objects.create(
        url='http://exams.com/exam_2015',
        exam=url_exam_2015,
        scraped_pdf=exam_2015_pdf,
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
                2015: {
                    'Vår': {
                        'exams': {'Engelsk': [exam_2015_url]},
                        'solutions': {},
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


class TestExamClassification:

    @pytest.mark.django_db
    def test_classify_pdf(self):
        """Exam type should be determinable from pdf content."""
        # The PDF contains the following content
        sha1_hash = '0000000000000000000000000000000000000000'
        pdf = Pdf(sha1_hash=sha1_hash)
        text = """
            NTNU TMA4115 Matematikk 3
            Institutt for matematiske fag
            eksamen 11.08.05
            Eksamenssettet har 12 punkter.
        """
        content = ContentFile(text)
        pdf.file.save(content=content, name=sha1_hash, save=True)

        # No errors should be raised when no pages has been saved yet, but
        # False should be returned to indicate a lack of success.
        pdf.classify(allow_ocr=True) is False  # Malformed plain text PDF
        pdf.classify(allow_ocr=False) is False

        assert pdf.content_type is None
        assert pdf.exams.count() == 0

        # But now we add a cover page and classify its content
        PdfPage.objects.create(text=text, pdf=pdf, number=0)
        pdf.refresh_from_db()
        print(pdf.pages.first().text)
        assert pdf.classify() is True

        # It should now be determined that the pdf contains an exam
        assert pdf.content_type == 'Exam'

        # And all metadata should be saved
        pdf = Pdf.objects.get(id=pdf.id)
        assert pdf.exams.count() == 1
        exam = pdf.exams.first()
        assert exam.language == Language.BOKMAL
        assert exam.course_code == 'TMA4115'
        assert exam.solutions is False
        assert exam.year == 2005
        assert exam.season == Season.CONTINUATION

        # When the classification method changes it result, old results
        # should be removed. This is simulated here by mutating the exam.
        exam.year == 1999
        exam.save()
        pdf.classify()
        pdf = Pdf.objects.get(id=pdf.id)
        assert pdf.exams.count() == 1
        assert pdf.exams.first().year == 2005

        # But verified exams should NOT be deleted
        verified_exam = Exam.objects.create(
            year=1999,
            course_code=exam.course_code,
            language=exam.language,
            solutions=exam.solutions,
        )
        user = UserFactory.create(username='verifier')
        verified_exam_pdf = ExamPdf.objects.create(exam=verified_exam, pdf=pdf)
        verified_exam_pdf.verified_by.add(user)
        pdf.classify()
        pdf = Pdf.objects.get(id=pdf.id)
        assert pdf.exams.count() == 2

    @pytest.mark.django_db
    def test_classify_pdf_with_several_course_codes(self):
        """Several course codes should be supported for exam PDFs."""
        sha1_hash = '0000000000000000000000000000000000000000'
        pdf = Pdf(sha1_hash=sha1_hash)
        text = """
            Exsamen i TMA4000/10 og TIØ4000
            Dato: 11.08.99
            Løsningsforslag
        """
        content = ContentFile(text)
        pdf.file.save(content=content, name=sha1_hash, save=True)
        PdfPage.objects.create(text=text, pdf=pdf, number=0)
        pdf.classify()
        assert (
            set(pdf.exams.values_list('course_code', flat=True)) ==
            {'TMA4000', 'TMA4010', 'TIØ4000'}
        )

        for exam in pdf.exams.all():
            assert exam.year == 1999
            assert exam.season == Season.CONTINUATION
            assert exam.language == Language.BOKMAL
            assert exam.solutions is True

    @pytest.mark.django_db
    def test_combining_urls_and_content_for_classification(self):
        """Exam classification should OR combine PDF and URL parsing."""
        sha1_hash = '0000000000000000000000000000000000000000'
        pdf = Pdf.objects.create(sha1_hash=sha1_hash)
        text = """
            Exsamen i TMA4000
            Dato: USPESIFISERT
            Løsningsforslag
        """
        PdfPage.objects.create(text=text, pdf=pdf, number=0)

        # The first URL is disregarded as the other two are more popular
        urls = [
            'http://wiki.math.ntnu.no/TMA4000/exams/2017_kont.pdf',
            'http://wiki.math.ntnu.no/TMA4000/exams/h2018.pdf',
            'http://wiki.math.ntnu.no/TMA4000/exams/2018h.pdf',
        ]
        for url in urls:
            pdf_url = PdfUrl.objects.create(url=url, scraped_pdf=pdf)
            assert pdf_url.exam.year and pdf_url.exam.season

        pdf.classify()
        assert pdf.exams.count() == 1

        exam = pdf.exams.first()
        assert exam.course_code == 'TMA4000'
        assert exam.solutions is True
        assert exam.language == Language.BOKMAL
        assert exam.year == 2018
        assert exam.season == Season.AUTUMN

    @pytest.mark.django_db
    def test_classifiying_bad_content(self):
        """Classification should handle onle Nones."""
        sha1_hash = '0000000000000000000000000000000000000000'
        pdf = Pdf.objects.create(sha1_hash=sha1_hash)
        text = 'Bad OCR!'
        PdfPage.objects.create(text=text, pdf=pdf, number=0)

        # First handle bad OCR without any URLs
        pdf.classify()
        assert pdf.exams.count() == 1

        exam = pdf.exams.first()
        assert exam.solutions is False
        assert exam.course_code is None
        assert exam.language is None
        assert exam.year is None
        assert exam.season is None

        # And handle bad OCR with bad URLs
        urls = [
            'http://bad.url/1.pdf',
            'http://bad.url/2.pdf',
            'http://bad.url/3.pdf',
        ]
        for url in urls:
            PdfUrl.objects.create(url=url, scraped_pdf=pdf)

        pdf.classify()
        assert pdf.exams.count() == 1

        exam = pdf.exams.first()
        assert exam.solutions is False
        assert exam.course_code is None
        assert exam.language is None
        assert exam.year is None
        assert exam.season is None

    @pytest.mark.django_db
    def test_using_courses_from_url_in_classification(self):
        """Exam course classification should AND combine PDF and URL parsing."""
        sha1_hash = '0000000000000000000000000000000000000000'
        pdf = Pdf.objects.create(sha1_hash=sha1_hash)

        # 1 course in exam
        text = "Exsamen i TMA4000"
        PdfPage.objects.create(text=text, pdf=pdf, number=0)

        # 3 additional courses in URL parsing
        urls = [
            'http://wiki.math.ntnu.no/TMA4100/exams/problems.pdf',
            'http://wiki.math.ntnu.no/TMA4200/exams/problems.pdf',
            'http://wiki.math.ntnu.no/TMA4300/exams/problems.pdf',
        ]
        for url in urls:
            PdfUrl.objects.create(url=url, scraped_pdf=pdf)

        # Results in 4 courses all together
        pdf.classify()
        assert pdf.exams.count() == 4
        assert (
            set(pdf.exams.values_list('course_code', flat=True)) ==
            {'TMA4000', 'TMA4100', 'TMA4200', 'TMA4300'}
        )

    @pytest.mark.django_db
    def test_determining_solutions_of_exam_without_content(self):
        """Solutions should by OR determined."""
        sha1_hash = '0000000000000000000000000000000000000000'
        pdf = Pdf.objects.create(sha1_hash=sha1_hash)

        text = "Bad OCR handwritten content"
        PdfPage.objects.create(text=text, pdf=pdf, number=0)

        # Only one url contains solutions but it is completely trusted
        urls = [
            'http://wiki.math.ntnu.no/TMA4000/exams/problems1.pdf',
            'http://wiki.math.ntnu.no/TMA4000/exams/problems2.pdf',
            'http://wiki.math.ntnu.no/TMA4000/exams/problems3_solutions.pdf',
        ]
        for url in urls:
            PdfUrl.objects.create(url=url, scraped_pdf=pdf)

        # Results in 4 courses all together
        pdf.classify()
        assert pdf.exams.count() == 1
        assert pdf.exams.first().solutions is True


class TestExamRelatedCourse:
    """Tests for ExamRelatedCourse."""

    @pytest.mark.django_db
    def test_deriving_course_from_course_code(self):
        """Secondary course should be derived from secondary course code."""
        primary = CourseFactory(course_code='TMA4122')
        secondary = CourseFactory(course_code='SIF5013')
        relation = ExamRelatedCourse.objects.create(
            primary_course=primary,
            secondary_course_code='SIF5013',
        )
        assert relation.secondary_course.id == secondary.id

    @pytest.mark.django_db
    def test_when_course_cant_be_derived_from_course_code(self):
        """Secondary course might not always exist in database."""
        primary = CourseFactory(course_code='TMA4122')
        relation = ExamRelatedCourse.objects.create(
            primary_course=primary,
            secondary_course_code='SIF5013',
        )
        assert relation.secondary_course is None

    @pytest.mark.django_db
    def test_creating_two_primary_courses_for_one_secondary_course(self):
        """One secondary course can't have two primary courses."""
        primary = CourseFactory(course_code='TMA4122')
        new_primary = CourseFactory(course_code='TMA4123')

        ExamRelatedCourse.objects.create(
            primary_course=primary,
            secondary_course_code='SIF5013',
        )
        with pytest.raises(ValidationError):
            ExamRelatedCourse.objects.create(
                primary_course=new_primary,
                secondary_course_code='SIF5013',
            )

    @pytest.mark.django_db
    def test_setting_a_primary_course_as_a_secondary_one(self):
        """A course can't be secondary and primary at the same time."""
        primary = CourseFactory(course_code='TMA4122')
        another_primary = CourseFactory(course_code='TMA4123')

        ExamRelatedCourse.objects.create(
            primary_course=primary,
            secondary_course_code='SIF5013',
        )
        with pytest.raises(ValidationError):
            ExamRelatedCourse.objects.create(
                primary_course=another_primary,
                secondary_course_code='TMA4122',
            )

    @pytest.mark.django_db
    def test_primary_course_with_several_secondary_courses(self):
        """But one primary course may have several secondary ones."""
        primary = CourseFactory(course_code='TMA4122')

        ExamRelatedCourse.objects.create(
            primary_course=primary,
            secondary_course_code='SIF5013',
        )
        ExamRelatedCourse.objects.create(
            primary_course=primary,
            secondary_course_code='SIF5014',
        )
        assert primary.secondary_courses.count() == 2
