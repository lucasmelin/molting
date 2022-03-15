import re
from datetime import datetime
from pathlib import Path
from subprocess import run
import argparse

RE_REPOSITORY = re.compile(r'^repository = "(?P<repository>.*)"$', re.MULTILINE)
RE_PYPROJECT_VERSION = re.compile(r'version = "(?P<version>\d+\.\d+(\.\d+)?)"')
RE_INIT_VERSION = re.compile(r'__version__ = "(?P<version>\d+\.\d+(\.\d+)?)"')
RE_LINK = re.compile(r"^\[(.*)\]: (.*)$")


class Project:
    project_directory: Path

    def __init__(self, project_directory: Path) -> None:
        self.project_directory = Path(project_directory)

    def get_repository(self) -> str:
        """Returns the repository URL.

        Raises:
            ValueError: The repository section in `pyproject.toml`
            couldn't be parsed.

        Returns:
            str: Full URL of the repository
        """
        pyproject = self.project_directory / "pyproject.toml"
        match = RE_REPOSITORY.search(pyproject.read_text())
        if not match:
            raise ValueError(f"Could not find repository in {pyproject}")
        return match.group("repository")

    def get_version(self) -> str:
        """Parses project version from `pyproject.toml`

        Returns:
            str: Current project version
        """
        pyproject = self.project_directory / "pyproject.toml"
        match = RE_PYPROJECT_VERSION.search(pyproject.read_text())
        if not match:
            raise ValueError(f"Could not find version in {pyproject}")
        return match.group("version")

    def update_pyproject(self, version_number: str):
        """Update the version found in `pyproject.toml`.

        Args:
            version_number (str): _description_
        """
        pyproject = self.project_directory / "pyproject.toml"
        file_text = pyproject.read_text()
        new_text = RE_PYPROJECT_VERSION.sub(f'version = "{version_number}"', file_text)
        pyproject.write_text(new_text)

    def update_init(
        self,
        version_number: str,
    ):
        """Update the version found in `__init__.py`.

        Args:
            version_number (str): New version number
        """
        init_files = self.project_directory.glob("**/__init__.py")
        for init in init_files:
            file_text = init.read_text()
            new_text = RE_INIT_VERSION.sub(
                f'__version__ = "{version_number}"', file_text
            )
            init.write_text(new_text)

    def update_changelog(self, old_version_number: str, version_number: str):
        """Update `CHANGELOG.md` for the new version.

        Args:
            old_version_number (str): Previous version
            version_number (str): Version to be released
        """
        changelog = self.project_directory / "CHANGELOG.md"
        file_text = changelog.read_text()
        file_text = file_text.replace(
            "## [Latest Changes]",
            f"## [Latest Changes]\n\n## [{version_number}] - {datetime.now():%Y-%m-%d}",
        )
        repository = self.get_repository()

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

    def extract_changelog_notes(self):
        """Parse the CHANGELOG.md and retun the latest unreleased changes.

        Args:
            project_directory (Path): Path to the current project

        Returns:
            str: Description of the changes
        """
        changelog = self.project_directory / "CHANGELOG.md"
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
            if RE_LINK.fullmatch(line) is not None:
                pass
            elif line.startswith("## ["):
                # New version, no need to look at the rest of the lines
                break
            elif not line.strip():
                pass
            else:
                latest_changes.append(line)
        return "\n".join(latest_changes)


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
    run("git", "add", ".")
    run("git", "commit", "-m", f"Bump version to v{version}")
    run("git", "tag", f"v{version}")
    run("git", "push")
    run("git", "push", "--tags")


def create_github_release(version: str, notes: str):
    """Create a new GitHub release.

    Depends on the GitHub CLI.

    Args:
        version (str): Version tag to release. If a matching git tag does not
        exist yet, one will automatically be created.
        notes (str): Release notes.
    """
    run(
        "gh",
        "release",
        "create",
        f"v{version}",
        "--title",
        f"v{version}",
        "--notes",
        notes,
    )


def get_commit_messages(starting_version: str, ending_version: str = "HEAD"):
    """Get the commit messages from the current git branch.

    Depends on `git`.

    Args:
        starting_version (str): Starting version number, not included in the results
        ending_version (str): Ending version number, defaults to HEAD

    Returns:
        list: List of commit message lines
    """
    log_lines = run(
        [
            "git",
            "--no-pager",
            "log",
            "--format=%B",
            f"{starting_version}...{ending_version}",
        ],
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return [line for line in log_lines if line.strip()]


def guess_change_type(lines: str) -> str:
    """Guess the change type based on the commit message."""
    # Default to patch version
    current_guess = "patch"
    minor_words = ["feat", "change", "improve"]
    for line in lines:
        # If breaking is found, immediately guess major without considering the
        # rest of the lines
        if "breaking" in line.lower():
            return "major"

        # If we come across a minor version word, change our guess
        if any(minor_word in line.lower() for minor_word in minor_words):
            current_guess = "minor"

    # Will either be patch or minor at this point
    return current_guess


def bump(project_directory: Path, version_part: str = None, dry_run: bool = True):
    project = Project(project_directory)
    old_version = project.get_version()
    commit_messages = get_commit_messages(old_version)

    if not version_part:
        version_part = guess_change_type(commit_messages)

    version = increase_version_number(old_version, version_part)

    print(f"Bumping the {version_part!r} version to {version!r}")

    if not dry_run:
        project.update_changelog(old_version, version)
        project.update_pyproject(version)
        project.update_init(version)
        print(f"Bumped files from {old_version!r} to {version!r}")
        print("Pushing the new tag")
        create_tag(version)
        notes = project.extract_changelog_notes()
        # If empty, use the commit messages
        if not notes:
            notes = commit_messages

        create_github_release(version, notes)

    else:
        notes = project.extract_changelog_notes()
        # If empty, use the commit messages
        if not notes:
            notes = commit_messages
        print(f"Changelog notes: \n {notes}")


def cli():
    parser = argparse.ArgumentParser("Kicks off an automated bump and release process.")
    parser.add_argument(
        "version",
        type=str,
        nargs="?",
        help="The type of semver release to make.",
        choices={"major", "minor", "patch"},
    )
    parser.add_argument("--project-dir", "-d", nargs="?", default=Path("."))
    parser.add_argument(
        "--dryrun",
        dest="dry_run",
        action="store_true",
        help="Don't make any changes, just print out what would happen",
    )
    args = parser.parse_args()
    bump(args.project_directory, args.version_part, args.dry_run)


if __name__ == "__main__":
    cli()
