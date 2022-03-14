import re
from datetime import datetime
from pathlib import Path
from subprocess import call

REPOSITORY = "https://github.com/lucasmelin/molt/"
RE_REPOSITORY = re.compile(r'^repository = "(?P<repository>.*)"$', re.MULTILINE)
RE_PYPROJECT_VERSION = re.compile(r'version = "(?P<version>\d+\.\d+(\.\d+)?)"')
RE_INIT_VERSION = re.compile(r'__version__ = "(?P<version>\d+\.\d+(\.\d+)?)"')


def get_repository(project_directory: Path) -> str:
    """Returns the repository URL.

    Raises:
        ValueError: The repository section in `pyproject.toml`
          couldn't be parsed.

    Returns:
        str: Full URL of the repository
    """
    if REPOSITORY:
        return REPOSITORY
    pyproject = project_directory / "pyproject.toml"
    match = RE_REPOSITORY.search(pyproject.read_text())
    if not match:
        raise ValueError(f"Could not find repository in {pyproject}")
    return match.group("repository")


def update_pyproject(version_number: str, project_directory: Path):
    """Update the version found in `pyproject.toml`.

    Args:
        version_number (str): _description_
    """
    pyproject = project_directory / "pyproject.toml"
    file_text = pyproject.read_text()
    new_text = RE_PYPROJECT_VERSION.sub(f'version = "{version_number}"', file_text)
    pyproject.write_text(new_text)


def update_init(version_number: str, project_directory: Path):
    """Update the version found in `__init__.py`.

    Args:
        version_number (str): New version number
    """
    init = project_directory / "src" / "molting" / "__init__.py"
    file_text = init.read_text()
    new_text = RE_INIT_VERSION.sub(f'__version__ = "{version_number}"', file_text)
    init.write_text(new_text)


def update_changelog(
    old_version_number: str, version_number: str, project_directory: Path
):
    """Update `CHANGELOG.md` for the new version.

    Args:
        old_version_number (str): Previous version
        version_number (str): Version to be released
    """
    changelog = project_directory / "CHANGELOG.md"
    file_text = changelog.read_text()
    file_text = file_text.replace(
        "## [Latest Changes]",
        f"## [Latest Changes]\n\n## [{version_number}] - {datetime.now():%Y-%m-%d}",
    )
    repository = get_repository(project_directory)

    # Update links at the bottom of the GHANGELOG
    if re.search(r"^\[Latest Changes\]:.*$", file_text, flags=re.MULTILINE):
        file_text = re.sub(
            r"^\[Latest Changes\]:.*$",
            "\n".join(
                [
                    f"[Latest Changes]: {repository}compare/v{version_number}...HEAD",
                    f"[{version_number}]: {repository}compare/v{old_version_number}...v{version_number}",
                ]
            ),
            file_text,
            flags=re.MULTILINE,
        )
    else:
        file_text = "\n\n".join(
            [
                file_text,
                f"[Latest Changes]: {repository}compare/v{version_number}...HEAD",
            ]
        )

    changelog.write_text(file_text)


def increase_version_number(version_number: str, version_part: str) -> str:
    """Increment the current version number according to SemVer type.

    Args:
        version_number (str): Current version number
        version_part (str): SemVer version part, one of `patch`, `minor` or `major`

    Returns:
        str: New version number
    """
    version_split = list(map(int, version_number.split(".")))

    if len(version_split) == 2:
        version_split.append(0)

    if version_part == "patch":
        version_split[2] += 1
    elif version_part == "minor":
        version_split[1] += 1
        version_split[2] = 0
    elif version_part == "major":
        version_split[0] += 1
        version_split[1] = 0
        version_split[2] = 0

    return ".".join(map(str, version_split))


def create_tag(version: str):
    """Create a tag for the specified version.

    Depends on `git`.

    Args:
        version (str): Version number to use for the tag
    """
    call("git", "add", ".")
    call("git", "commit", "-m", f"Bump version to v{version}")
    call("git", "tag", f"v{version}")
    call("git", "push")
    call("git", "push", "--tags")


def create_github_release(version: str, notes: str):
    """Create a new GitHub release.

    Depends on the GitHub CLI.

    Args:
        version (str): Version tag to release. If a matching git tag does not
          exist yet, one will automatically be created.
        notes (str): Release notes.
    """
    call(
        "gh",
        "release",
        "create",
        f"v{version}",
        "--title",
        f"v{version}",
        "--notes",
        notes,
    )


link_pattern = re.compile(r"^\[(.*)\]: (.*)$")


def extract_changelog_notes(project_directory: Path):
    """Parse the CHANGELOG.md and retun the latest unreleased changes.

    Args:
        project_directory (Path): Path to the current project

    Returns:
        str: Description of the changes
    """
    changelog = project_directory / "CHANGELOG.md"
    file_text = changelog.read_text()
    file_lines = file_text.splitlines()
    index = [
        idx
        for idx, line in enumerate(file_lines)
        if line.startswith("## [Latest Changes]")
    ][0]
    after_latest = file_lines[index + 1 :]
    latest_changes = []
    for line in after_latest:
        if link_pattern.fullmatch(line) is not None:
            pass
        elif line.startswith("## ["):
            # New version, no need to look at the rest of the lines
            break
        elif not line.strip():
            pass
        else:
            latest_changes.append(line)
    return "\n".join(latest_changes)
