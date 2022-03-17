"""molting main."""
import argparse
import re
import sys
from datetime import datetime
from functools import partial
from pathlib import Path
from subprocess import CalledProcessError, run

from loguru import logger

RE_REPOSITORY = re.compile(
    r'^repository = (["\'])(?P<repository>.*)(["\'])$', re.MULTILINE
)
RE_PYPROJECT_VERSION = re.compile(
    r'version = (["\'])(?P<version>\d+\.\d+(\.\d+)?)(["\'])'
)
RE_INIT_VERSION = re.compile(
    r'__version__ = (["\'])(?P<version>\d+\.\d+(\.\d+)?)(["\'])'
)
RE_NAME = re.compile(r'^name = (["\'])(?P<name>.*)(["\'])$', re.MULTILINE)
RE_LINK = re.compile(r"^\[(.*)\]: (.*)$")


def combine_items(items, callable):
    """Combine a list of strings, and then pass them into a provided function.

    Useful for logging a list of strings as a single command.
    """
    args = " ".join(items)
    return callable(args)


class Project:
    """Data and methods for a project."""

    project_directory: Path
    dry_run: bool

    def __init__(self, project_directory: Path, dry_run: bool) -> None:
        """Initialize Project."""
        self.project_directory = Path(project_directory)
        self.dry_run = dry_run

    def get_repository(self) -> str:
        """Returns the repository URL.

        Raises:
            ValueError: The repository section in `pyproject.toml`
            couldn't be parsed.

        Returns:
            str: Full URL of the repository
        """
        pyproject = self.project_directory / "pyproject.toml"
        logger.debug(f"Searching for `repository` in {pyproject.resolve()}")
        match = RE_REPOSITORY.search(pyproject.read_text())
        if not match:
            raise ValueError(f"Could not find repository in {pyproject}")
        repository = match.group("repository")
        if not repository.endswith("/"):
            repository = f"{repository}/"
        logger.debug(f"Found repository {repository!r} in pyproject.toml")
        return repository

    def get_name(self) -> str:
        """Returns the project name.

        Raises:
            ValueError: The name section in `pyproject.toml`
            couldn't be parsed.

        Returns:
            str: Name of the project
        """
        pyproject = self.project_directory / "pyproject.toml"
        logger.debug(f"Searching for `name` in {pyproject.resolve()}")
        match = RE_NAME.search(pyproject.read_text())
        if not match:
            raise ValueError(f"Could not find name in {pyproject}")
        name = match.group("name")
        logger.debug(f"Found name {name!r} in pyproject.toml")
        return name

    def get_version(self) -> str:
        """Parses project version from `pyproject.toml`.

        Returns:
            str: Current project version
        """
        pyproject = self.project_directory / "pyproject.toml"
        logger.debug(f"Searching for `version` in {pyproject.resolve()}")
        match = RE_PYPROJECT_VERSION.search(pyproject.read_text())
        if not match:
            raise ValueError(f"Could not find version in {pyproject}")
        version = match.group("version")
        logger.debug(f"Found version {version!r} in pyproject.toml")
        return version

    def update_pyproject(self, version_number: str):
        """Update the version found in `pyproject.toml`.

        Args:
            version_number (str): _description_
        """
        pyproject = self.project_directory / "pyproject.toml"
        file_text = pyproject.read_text()
        new_text = RE_PYPROJECT_VERSION.sub(f'version = "{version_number}"', file_text)
        logger.debug("Writing pyproject.toml changes")
        if self.dry_run:
            logger.trace(new_text)
        else:
            pyproject.write_text(new_text)

    def update_init(self, version_number: str, project_name: str):
        """Update the version found in `__init__.py`.

        Will not add a version string if one doesn't already exist in the file.

        Args:
            version_number (str): New version number
            project_name (str): Name of the python project containing __init__
              files
        """
        init_files = self.project_directory.glob(f"src/{project_name}/**/__init__.py")
        for init in init_files:
            logger.debug(f"Searching for `__version__` in {init.resolve()}")
            file_text = init.read_text()
            new_text = RE_INIT_VERSION.sub(
                f'__version__ = "{version_number}"', file_text
            )
            logger.debug("Writing __init__.py changes")
            if self.dry_run:
                logger.trace(new_text)
            else:
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
            logger.debug("Found [Latest Changes] section")
            file_text = re.sub(
                r"^\[Latest Changes\]:.*$",
                "\n".join(
                    [
                        f"[Latest Changes]: {repository}compare/v{version_number}...HEAD",
                        f"[{version_number}]: "
                        f"{repository}compare/v{old_version_number}...v{version_number}",
                    ]
                ),
                file_text,
                flags=re.MULTILINE,
            )
        else:
            logger.debug("Didn't find [Latest Changes] section")
            file_text = "\n\n".join(
                [
                    file_text,
                    f"[Latest Changes]: {repository}compare/v{version_number}...HEAD",
                ]
            )
        logger.debug(f"Moving change notes from [Latest Changes] to v{version_number}")
        if self.dry_run:
            logger.trace(file_text)
        else:
            changelog.write_text(file_text)

    def extract_changelog_notes(self):
        """Parse the CHANGELOG.md and return the latest unreleased changes.

        Args:
            project_directory (Path): Path to the current project

        Returns:
            str: Description of the changes
        """
        changelog = self.project_directory / "CHANGELOG.md"
        logger.debug(f"Searching for changelog notes in {changelog}")
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
        notes = "\n".join(latest_changes)
        line_count = notes.count("\n") + 1 if notes else 0
        logger.debug(f"Found {line_count} notes in CHANGELOG.md")
        return notes

    def add_changelog_notes(self, notes: str):
        """Add notes to the `Latest Changes` section in `CHANGELOG.md`.

        Args:
            notes (str): Notes to add
        """
        changelog = self.project_directory / "CHANGELOG.md"
        logger.debug(f"Adding to [Latest Changes] section in {changelog}")
        file_text = changelog.read_text()
        file_text = file_text.replace(
            "## [Latest Changes]", f"## [Latest Changes]\n{notes}"
        )
        if self.dry_run:
            logger.trace(file_text)
        else:
            changelog.write_text(file_text)

    def create_tag(self, version: str):
        """Create a tag for the specified version.

        Depends on `git`.

        Args:
            version (str): Version number to use for the tag
        """
        logger.info(f"Creating git tag for {version!r}")
        if self.dry_run:
            run_command = partial(combine_items, callable=logger.debug)
        else:
            run_command = partial(run, text=True, cwd=self.project_directory)
        run_command(["git", "add", "."])
        run_command(["git", "commit", "-m", f"Bump version to v{version}"])
        run_command(["git", "tag", f"v{version}"])
        run_command(["git", "push"])
        run_command(["git", "push", "--tags"])

    def create_github_release(self, version: str, notes: str):
        """Create a new GitHub release.

        Depends on the GitHub CLI.

        Args:
            version (str): Version tag to release. If a matching git tag does not
            exist yet, one will automatically be created.
            notes (str): Release notes.
        """
        logger.info(f"Creating GitHub release for {version!r}")
        if self.dry_run:
            run_command = partial(combine_items, callable=logger.debug)
        else:
            run_command = partial(run, text=True, cwd=self.project_directory)
        run_command(
            [
                "gh",
                "release",
                "create",
                f"v{version}",
                "--title",
                f"v{version}",
                "--notes",
                notes,
            ]
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
    run_command = partial(run, capture_output=True, text=True)
    try:
        # If this executes successfully, then the version exists locally
        result = run_command(["git", "rev-parse", starting_version], check=True)
        result.check_returncode()
        logger.debug(f"Found git ref for {starting_version!r}")
    except CalledProcessError:
        logger.debug(f"Didn't find git ref {starting_version!r}")
        # Couldn't find the starting version, so instead get the initial repo commit
        starting_version = run_command(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
        ).stdout[:7]
        logger.debug(f"Using git ref {starting_version!r} as starting point")

    log_lines = run_command(
        [
            "git",
            "--no-pager",
            "log",
            "--format=%B",
            f"{starting_version}...{ending_version}",
        ],
    ).stdout.splitlines()
    non_empty_lines = [line for line in log_lines if line.strip()]
    logger.debug(f"Found {len(non_empty_lines)} lines")
    return non_empty_lines


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


def guess_change_type(lines: str) -> str:
    """Guess the change type based on the commit message."""
    # Default to patch version
    logger.debug("Attempting to guess change type")
    current_guess = "patch"
    minor_words = ["feat", "change", "improve"]
    for line in lines:
        # If breaking is found, immediately guess major without considering the
        # rest of the lines
        if "breaking" in line.lower():
            logger.debug(f"Found `major` version keyword in {line}")
            return "major"

        # If we come across a minor version word, change our guess
        if any(minor_word in line.lower() for minor_word in minor_words):
            logger.debug(f"Found `minor` version keyword in {line}")
            current_guess = "minor"

    logger.debug(f"Guessing change is {current_guess!r}")
    # Will either be patch or minor at this point
    return current_guess


def bump(project_directory: Path, version_part: str = None, dry_run: bool = True):
    """Bump the project files to the latest version and generate a release.

    Args:
        project_directory (Path): Project root directory
        version_part (str, optional): Version to bump, one of `patch`, `minor`
          or `major`. If not specified, then the commit messages will be parsed
          in order to formulate a guess.
        dry_run (bool, optional): Don't make any changes, just print out what
          would happen. Defaults to True.
    """
    project = Project(project_directory, dry_run)
    old_version = project.get_version()
    commit_messages = get_commit_messages(f"v{old_version}")

    if not version_part:
        version_part = guess_change_type(commit_messages)

    version = increase_version_number(old_version, version_part)

    logger.info(f"Bumping the {version_part!r} version to {version!r}")

    notes = project.extract_changelog_notes()

    # If empty, use the commit messages
    if not notes:
        logger.info("Using the commit messages as changelog notes")
        notes = "\n - ".join(["", *commit_messages])
        project.add_changelog_notes(notes)
    project.update_changelog(old_version, version)
    project.update_pyproject(version)
    project_name = project.get_name()
    project.update_init(version, project_name)
    logger.info(f"Bumped files from {old_version!r} to {version!r}")
    project.create_tag(version)
    project.create_github_release(version, notes)


def cli():
    """Handle command-line arguments."""
    parser = argparse.ArgumentParser("Kicks off an automated bump and release process.")
    parser.add_argument(
        "version",
        type=str,
        nargs="?",
        help="The type of semver release to make.",
        choices={"major", "minor", "patch"},
    )
    parser.add_argument("--project-directory", "-d", nargs="?", default=Path("."))
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Don't make any changes, just print out what would happen",
    )
    parser.add_argument(
        "-log",
        "--log",
        default="warning",
        help=("Provide logging level. " "Example --log debug', default='warning'"),
        choices={"critical", "error", "warning", "success", "info", "debug", "trace"},
    )
    args = parser.parse_args()
    logger.remove()
    log_level = "TRACE" if args.dry_run else args.log.upper()
    logger.add(sys.stderr, level=log_level)
    logger.debug(f"Args: {args}")
    bump(args.project_directory, args.version, args.dry_run)


if __name__ == "__main__":
    cli()
