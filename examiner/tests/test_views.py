from django.core.files.base import ContentFile
from django.shortcuts import reverse

import pytest

from examiner.models import DocumentInfo, ExamPdf, Pdf


@pytest.mark.django_db
def test_empty_exams_view(client):
    """Test empty output of all exams view when no URL is present."""
    response = client.get(reverse('examiner:all_exams'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_verify_view(client):
    """Test PDF verification view."""
    pdf = Pdf.objects.create()
    content = ContentFile('exam text')
    pdf.file.save(name='file', content=content)
    exam = DocumentInfo.objects.create()
    ExamPdf.objects.create(pdf=pdf, exam=exam)
    response = client.get(reverse('examiner:verify_random'))
    assert response.status_code == 200
