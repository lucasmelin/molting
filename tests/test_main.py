import pytest
from molting.main import increase_version_number


@pytest.mark.parametrize(
    "old_version,expected_version",
    [("0.1.0", "0.1.1"), ("1.0.0", "1.0.1"), ("0.0.1", "0.0.2"), ("0.1.1", "0.1.2")],
)
def test_increase_patch(old_version, expected_version):
    version = increase_version_number(old_version, "patch")
    assert version == expected_version


@pytest.mark.parametrize(
    "old_version,expected_version",
    [("0.1.0", "0.1.1"), ("1.0.0", "1.0.1"), ("0.0.1", "0.0.2"), ("0.1.1", "0.1.2")],
)
def test_increase_minor(old_version, expected_version):
    version = increase_version_number(old_version, "patch")
    assert version == expected_version


@pytest.mark.parametrize(
    "old_version,expected_version",
    [("0.1.0", "0.2.0"), ("1.0.0", "1.2.0"), ("0.0.1", "0.1.0"), ("0.1.1", "0.2.0")],
)
def test_increase_major(old_version, expected_version):
    version = increase_version_number(old_version, "minor")
    assert version == expected_version


@pytest.mark.parametrize(
    "old_version,expected_version",
    [("0.1.0", "1.0.0"), ("1.0.0", "2.0.0"), ("0.0.1", "1.0.0"), ("0.1.1", "1.0.0")],
)
def test_increase_major(old_version, expected_version):
    version = increase_version_number(old_version, "major")
    assert version == expected_version
