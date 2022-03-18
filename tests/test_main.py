import datetime
import textwrap

import pytest

from molting.main import (
    Project,
    combine_items,
    guess_change_type,
    increase_version_number,
)


@pytest.mark.parametrize(
    "old_version,expected_version",
    [
        ("0.1.0", "0.1.1"),
        ("1.0.0", "1.0.1"),
        ("0.0.1", "0.0.2"),
        ("0.1.1", "0.1.2"),
        ("0.1", "0.1.1"),
    ],
)
def test_increase_patch(old_version, expected_version):
    version = increase_version_number(old_version, "patch")
    assert version == expected_version


@pytest.mark.parametrize(
    "old_version,expected_version",
    [
        ("0.1.0", "0.2.0"),
        ("1.0.0", "1.1.0"),
        ("0.0.1", "0.1.0"),
        ("0.1.1", "0.2.0"),
        ("0.1", "0.2.0"),
    ],
)
def test_increase_minor(old_version, expected_version):
    version = increase_version_number(old_version, "minor")
    assert version == expected_version


@pytest.mark.parametrize(
    "old_version,expected_version",
    [
        ("0.1.0", "1.0.0"),
        ("1.0.0", "2.0.0"),
        ("0.0.1", "1.0.0"),
        ("0.1.1", "1.0.0"),
        ("0.1", "1.0.0"),
    ],
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


def test_update_init_dry_run(tmp_path):
    project_name = "project"
    d = tmp_path / "src" / project_name
    d.mkdir(parents=True)
    init = d / "__init__.py"
    old_version = "0.1.0"
    init.write_text(f'__version__ = "{old_version}"')
    project = Project(tmp_path, dry_run=True)
    project.update_init("0.2.0", project_name)
    assert init.read_text() == f'__version__ = "{old_version}"'


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


@pytest.mark.parametrize(
    "changes_title",
    [("Latest Changes"), ("Unreleased")],
)
def test_update_changelog_with_existing_change_links(tmp_path, mocker, changes_title):
    datetime_mock = mocker.patch("molting.main.datetime")
    datetime_mock.now.return_value = datetime.datetime(2022, 3, 1)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('repository = "https://example.com"')
    changelog = tmp_path / "CHANGELOG.md"
    change_notes = textwrap.dedent(
        f"""\
        ## [{changes_title}]

        - Here are some changes

        [{changes_title}]: https://example.com/compare/v0.1.0...HEAD"""
    )
    changelog.write_text(change_notes)
    project = Project(tmp_path, dry_run=False)
    project.update_changelog(old_version_number="0.1.0", version_number="0.2.0")
    assert changelog.read_text() == textwrap.dedent(
        f"""\
        ## [{changes_title}]

        ## [0.2.0] - 2022-03-01

        - Here are some changes

        [{changes_title}]: https://example.com/compare/v0.2.0...HEAD
        [0.2.0]: https://example.com/compare/v0.1.0...v0.2.0"""
    )


def test_update_changelog_dry_run(tmp_path, mocker):
    datetime_mock = mocker.patch("molting.main.datetime")
    datetime_mock.now.return_value = datetime.datetime(2022, 3, 1)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('repository = "https://example.com"')
    changelog = tmp_path / "CHANGELOG.md"
    change_notes = textwrap.dedent(
        """\
        ## [Latest Changes]

        - Here are some changes

        [Latest Changes]: https://example.com/compare/v0.1.0...HEAD"""
    )
    changelog.write_text(change_notes)
    project = Project(tmp_path, dry_run=True)
    project.update_changelog(old_version_number="0.1.0", version_number="0.2.0")
    assert changelog.read_text() == change_notes


def test_combine_items(capsys):
    items = ["aaa", "bbb", "ccc"]
    combine_items(items, print)
    captured = capsys.readouterr()
    assert captured.out == "aaa bbb ccc\n"


def test_update_changelog_missing_repository(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")
    changelog = tmp_path / "CHANGELOG.md"
    change_notes = textwrap.dedent(
        """\
        ## [Latest Changes]

        - Here are some changes"""
    )
    changelog.write_text(change_notes)
    project = Project(tmp_path, dry_run=False)
    with pytest.raises(ValueError, match=f"Could not find repository in {pyproject}"):
        project.update_changelog(old_version_number="0.1.0", version_number="0.2.0")


def test_get_project_name(tmp_path):
    expected_name = "example-name"
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'name = "{expected_name}"')
    project = Project(tmp_path, dry_run=False)
    actual_name = project.get_name()
    assert actual_name == expected_name


def test_get_project_name_does_not_exist(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")
    project = Project(tmp_path, dry_run=False)
    with pytest.raises(ValueError, match=f"Could not find name in {pyproject}"):
        project.get_name()


def test_get_version(tmp_path):
    expected_version = "0.1.0"
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'version = "{expected_version}"')
    project = Project(tmp_path, dry_run=False)
    actual_version = project.get_version()
    assert actual_version == expected_version


def test_get_version_does_not_exist(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")
    project = Project(tmp_path, dry_run=False)
    with pytest.raises(ValueError, match=f"Could not find version in {pyproject}"):
        project.get_version()


def test_update_pyproject(tmp_path):
    old_version = "0.1.0"
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'version = "{old_version}"')
    project = Project(tmp_path, dry_run=False)
    expected_version = "0.2.0"
    project.update_pyproject(expected_version)
    assert pyproject.read_text() == f'version = "{expected_version}"'


def test_update_pyproject_dry_run(tmp_path):
    old_version = "0.1.0"
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(f'version = "{old_version}"')
    project = Project(tmp_path, dry_run=True)
    project.update_pyproject("0.2.0")
    assert pyproject.read_text() == f'version = "{old_version}"'


def test_extract_changelog_notes(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")
    changelog = tmp_path / "CHANGELOG.md"
    change_notes = textwrap.dedent(
        """\
        ## [Latest Changes]

        - Here are some changes
        - Here are more changes"""
    )
    changelog.write_text(change_notes)
    project = Project(tmp_path, dry_run=False)
    notes = project.extract_changelog_notes()
    assert notes == "- Here are some changes\n- Here are more changes"


def test_extract_changelog_notes_no_new_changes(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")
    changelog = tmp_path / "CHANGELOG.md"
    change_notes = textwrap.dedent(
        """\
        ## [0.1.0]

        - Here are some changes
        - Here are more changes"""
    )
    changelog.write_text(change_notes)
    project = Project(tmp_path, dry_run=False)
    notes = project.extract_changelog_notes()
    assert notes == ""


def test_add_changelog_notes(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")
    changelog = tmp_path / "CHANGELOG.md"
    change_notes = textwrap.dedent(
        """\
        ## [Latest Changes]
        - Here are some changes
        - Here are more changes"""
    )
    changelog.write_text(change_notes)
    project = Project(tmp_path, dry_run=False)
    project.add_changelog_notes("- Something new")
    assert changelog.read_text() == textwrap.dedent(
        """\
        ## [Latest Changes]

        - Something new
        - Here are some changes
        - Here are more changes"""
    )


def test_guess_change_type_patch():
    messages = ["Add something new", "Fix a bug"]
    change_type = guess_change_type(messages)
    assert change_type == "patch"


def test_guess_change_type_minor():
    messages = ["New feature"]
    change_type = guess_change_type(messages)
    assert change_type == "minor"


def test_guess_change_type_major():
    messages = ["Add something new", "Fix a bug", "New feature", "Breaking change"]
    change_type = guess_change_type(messages)
    assert change_type == "major"
