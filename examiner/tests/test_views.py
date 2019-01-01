from django.core.files.base import ContentFile
from django.shortcuts import reverse

import pytest

from examiner.forms import VerifyExamForm
from examiner.models import DocumentInfo, DocumentInfoSource, Pdf
from semesterpage.tests.factories import CourseFactory


@pytest.mark.django_db
def test_empty_exams_view(client):
    """Test empty output of all exams view when no URL is present."""
    response = client.get(reverse('examiner:all_exams'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_verify_random_pdf_view(client, django_user_model):
    """Test PDF verification view."""
    # We have one PDF
    sha1_hash = '0000000000000000000000000000000000000000'
    pdf = Pdf(sha1_hash=sha1_hash)
    content = ContentFile('exam text')
    pdf.file.save(name=sha1_hash + '.pdf', content=content)

    # And three courses
    course1 = CourseFactory(course_code='TMA1000')
    course2 = CourseFactory(course_code='TMA2000')
    course3 = CourseFactory(course_code='TMA3000')

    # The PDF has been inferred to contain the two first of these courses
    common_docinfo_attrs = {
        'language': 'Bokmål',
        'year': 2010,
        'solutions': False,
        'content_type': 'Exam',
    }
    exam1 = DocumentInfo.objects.create(
        course=course1,
        **common_docinfo_attrs,
    )
    DocumentInfoSource.objects.create(pdf=pdf, document_info=exam1)

    exam2 = DocumentInfo.objects.create(
        course=course2,
        **common_docinfo_attrs,
    )
    DocumentInfoSource.objects.create(pdf=pdf, document_info=exam2)

    # We verify a random PDF in this case our PDF since there is only one
    user = django_user_model.objects.create_user(username='u', password='p')
    client.login(username='u', password='p')

    url = reverse('examiner:verify_random')
    response = client.get(url)
    assert response.status_code == 200

    # The form instance is populated with the first exam
    form = response.context['form']
    data = form.initial
    assert form.instance == exam1
    assert data['language'] == 'Bokmål'
    assert data['pdf'] == pdf
    assert data['season'] is None
    assert data['verifier'] == user

    # But both courses appear in the courses field
    assert data['courses'].count() == 2
    assert set(data['courses']) == {course1.id, course2.id}

    # The user now changes the 2 courses
    form = VerifyExamForm({
        'courses': [course2.id, course3.id],
        'pdf': pdf.id,
        'verifier': user.id,
        **common_docinfo_attrs,
    })
    assert form.is_valid()
    response = client.post(url, form.data)
    assert response.status_code == 302

    # We have two new verified exams
    verified_exams = DocumentInfoSource.objects.filter(verified_by__in=[user])
    assert verified_exams.count() == 2

    # Both are connected to our pdf
    exam_pdf1 = verified_exams.first()
    exam_pdf2 = verified_exams.last()
    assert exam_pdf1.pdf == pdf
    assert exam_pdf2.pdf == pdf
    assert exam_pdf1.verified_by.first() == user
    assert exam_pdf2.verified_by.first() == user

    # With two different courses
    docinfo1 = exam_pdf1.document_info
    docinfo2 = exam_pdf2.document_info
    assert docinfo1.course == course2
    assert docinfo2.course == course3

    # But all other attributes being equeal
    for key, value in common_docinfo_attrs.items():
        assert getattr(docinfo1, key) == value
        assert getattr(docinfo2, key) == value

    # The two other existing relations remain
    assert DocumentInfoSource.objects.filter(
        verified_by__isnull=True,
    ).count() == 2

    # And we have alltogether 3 DocumentInfo objects
    assert DocumentInfo.objects.count() == 3


@pytest.mark.django_db
def test_verify_pdf_view(admin_client):
    """Test PDF verification of specific model objects."""
    # We have one PDF
    sha1_hash = '0000000000000000000000000000000000000000'
    pdf = Pdf(sha1_hash=sha1_hash)
    content = ContentFile('exam text')
    pdf.file.save(name=sha1_hash + '.pdf', content=content)

    # And another one
    sha1_hash2 = '1111111111111111111111111111111111111111'
    pdf2 = Pdf(sha1_hash=sha1_hash2)
    content2 = ContentFile('exam text')
    pdf2.file.save(name=sha1_hash2 + '.pdf', content=content2)

    # Both PDFs are connected to the same exam
    exam = DocumentInfo.objects.create()
    DocumentInfoSource.objects.create(pdf=pdf, document_info=exam)
    DocumentInfoSource.objects.create(pdf=pdf2, document_info=exam)

    # And each resolves to a view with their own PDF as context
    response = admin_client.get(pdf.get_absolute_url())
    assert response.context['pdf'] == pdf
    response2 = admin_client.get(pdf2.get_absolute_url())
    assert response2.context['pdf'] == pdf2
