import pytest

from dataporten.tests.factories import DataportenUserFactory


@pytest.fixture
@pytest.mark.django_db
def dataporten_user():
    return DataportenUserFactory()
