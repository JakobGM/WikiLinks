from django.shortcuts import reverse

import pytest


@pytest.mark.django_db
def test_empty_exams_view(client):
    """Test empty output of all exams view when no URL is present."""
    response = client.get(reverse('examiner:all_exams'))
    assert response.status_code == 200
