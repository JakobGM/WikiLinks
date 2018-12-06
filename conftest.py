import pytest

@pytest.fixture(autouse=True)
def media_root(tmpdir, settings):
    settings.MEDIA_ROOT = tmpdir / 'media'
