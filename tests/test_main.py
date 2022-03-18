import datetime
import textwrap

import pytest

from molting.main import Project, increase_version_number


@pytest.mark.parametrize(
    "old_version,expected_version",
    [("0.1.0", "0.1.1"), ("1.0.0", "1.0.1"), ("0.0.1", "0.0.2"), ("0.1.1", "0.1.2")],
)
def test_increase_patch(old_version, expected_version):
    version = increase_version_number(old_version, "patch")
    assert version == expected_version


@pytest.mark.parametrize(
    "old_version,expected_version",
    [("0.1.0", "0.2.0"), ("1.0.0", "1.1.0"), ("0.0.1", "0.1.0"), ("0.1.1", "0.2.0")],
)
def test_increase_minor(old_version, expected_version):
    version = increase_version_number(old_version, "minor")
    assert version == expected_version


@pytest.mark.parametrize(
    "old_version,expected_version",
    [("0.1.0", "1.0.0"), ("1.0.0", "2.0.0"), ("0.0.1", "1.0.0"), ("0.1.1", "1.0.0")],
)
def test_increase_major(old_version, expected_version):
    version = increase_version_number(old_version, "major")
    assert version == expected_version


def test_update_init_double_quotes(tmp_path):
    project_name = "project"
    d = tmp_path / "src" / project_name
    d.mkdir(parents=True)
    init = d / "__init__.py"
    init.write_text('__version__ = "0.1.0"')
    project = Project(tmp_path, dry_run=False)
    project.update_init("0.2.0", project_name)
    assert init.read_text() == '__version__ = "0.2.0"'


def test_update_init_single_quotes(tmp_path):
    project_name = "project"
    d = tmp_path / "src" / project_name
    d.mkdir(parents=True)
    init = d / "__init__.py"
    init.write_text("__version__ = '0.1.0'")
    project = Project(tmp_path, dry_run=False)
    project.update_init("0.2.0", project_name)
    assert init.read_text() == '__version__ = "0.2.0"'


@pytest.mark.parametrize(
    "changes_title",
    [("Latest Changes"), ("Unreleased")],
)
def test_update_changelog_with_changes_title(tmp_path, mocker, changes_title):
    datetime_mock = mocker.patch("molting.main.datetime")
    datetime_mock.now.return_value = datetime.datetime(2022, 3, 1)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('repository = "https://example.com"')
    changelog = tmp_path / "CHANGELOG.md"
    change_notes = textwrap.dedent(
        f"""\
        ## [{changes_title}]

        - Here are some changes"""
    )
    changelog.write_text(change_notes)
    project = Project(tmp_path, dry_run=False)
    project.update_changelog(old_version_number="0.1.0", version_number="0.2.0")
    assert changelog.read_text() == textwrap.dedent(
        f"""\
        ## [{changes_title}]

        ## [0.2.0] - 2022-03-01

        - Here are some changes

        [{changes_title}]: https://example.com/compare/v0.2.0...HEAD"""
    )
