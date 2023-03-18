"""Tests of basic packaging and runtime metadata."""
import doitoml


def test_version() -> None:
    """Verify there is a version."""
    assert doitoml.__version__
