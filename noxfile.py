import nox
import argparse
import re
from datetime import datetime
from pathlib import Path

REPOSITORY = "https://github.com/lucasmelin/molt/"
RE_REPOSITORY = re.compile(r'^repository = "(?P<repository>.*)"$', re.MULTILINE)
RE_PYPROJECT_VERSION = re.compile(r'version = "(?P<version>\d+\.\d+(\.\d+)?)"')
RE_INIT_VERSION = re.compile(r'__version__ = "(?P<version>\d+\.\d+(\.\d+)?)"')


def get_repository() -> str:
    """Returns the repository URL.

    Raises:
        argparse.ArgumentTypeError: The repository section in `pyproject.toml`
          couldn't be parsed.

    Returns:
        str: Full URL of the repository
    """
    if REPOSITORY:
        return REPOSITORY
    pyproject = Path(__file__).parent / "pyproject.toml"
    match = RE_REPOSITORY.search(pyproject.read_text())
    if not match:
        raise argparse.ArgumentTypeError(f"Could not find repository in {pyproject}")
    return match.group("repository")


def update_pyproject(version_number: str):
    """Update the version found in `pyproject.toml`.

    Args:
        version_number (str): _description_
    """
    pyproject = Path(__file__).parent / "pyproject.toml"
    file_text = pyproject.read_text()
    new_text = RE_PYPROJECT_VERSION.sub(f'version = "{version_number}"', file_text)
    pyproject.write_text(new_text)


def update_init(version_number: str):
    """Update the version found in `__init__.py`.

    Args:
        version_number (str): New version number
    """
    init = Path(__file__).parent / "src" / "molt" / "__init__.py"
    file_text = init.read_text()
    new_text = RE_INIT_VERSION.sub(f'__version__ = "{version_number}"', file_text)
    init.write_text(new_text)


def update_changelog(old_version_number: str, version_number: str):
    """Update `CHANGELOG.md` for the new version.

    Args:
        old_version_number (str): Previous version
        version_number (str): Version to be released
    """
    changelog = Path(__file__).parent / "CHANGELOG.md"
    file_text = changelog.read_text()
    file_text = file_text.replace(
        "## [Latest Changes]",
        f"## [Latest Changes]\n\n## [{version_number}] - {datetime.now():%Y-%m-%d}",
    )
    repository = get_repository()

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


@nox.session
def release(session: nox.Session) -> None:
    """
    Kicks off an automated release process by creating and pushing a new tag.

    Usage:
    $ nox -s release -- [major|minor|patch]
    """
    parser = argparse.ArgumentParser(description="Release a semver version.")
    parser.add_argument(
        "version",
        type=str,
        nargs=1,
        help="The type of semver release to make.",
        choices={"major", "minor", "patch"},
    )
    args: argparse.Namespace = parser.parse_args(args=session.posargs)
    version_part: str = args.version.pop()

    # If we get here, we should be good to go
    # Let's do a final check for safety
    confirm = input(
        f"You are about to bump the {version_part!r} version. Are you sure? [y/n]: "
    )

    # Abort on anything other than 'y'
    if confirm.lower().strip() != "y":
        session.error(
            f"You said no when prompted to bump the {version_part!r} version."
        )

    session.log(f"Bumping the {version_part!r} version")
    from molt import __version__

    version = increase_version_number(__version__, version_part)

    update_changelog(__version__, version)
    update_pyproject(version)
    update_init(version)
    session.log(f"Bumped files from {__version__!r} to {version!r}")
    session.log("Pushing the new tag")

    # session.run("git", "add", ".")
    # session.run("git", "commit", "-m", f"Bump version to v{version}")
    # session.run("git", "tag", f"v{version}")
    # session.run("git", "push", external=True)
    # session.run("git", "push", "--tags", external=True)
