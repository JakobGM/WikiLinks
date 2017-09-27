import pytest

@pytest.mark.django_db
def test_dataporten_user_token(dataporten_user):
    assert dataporten_user.token == 'dummy_token'