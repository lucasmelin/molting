import nox
import argparse
from pathlib import Path
from molting.main import (
    increase_version_number,
    update_changelog,
    update_pyproject,
    update_init,
    create_tag,
    extract_changelog_notes,
    create_github_release
)


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
    from molting import __version__

    project_directory = Path(__file__).parent

    version = increase_version_number(__version__, version_part)

    update_changelog(__version__, version, project_directory)
    update_pyproject(version, project_directory)
    update_init(version, project_directory)
    session.log(f"Bumped files from {__version__!r} to {version!r}")
    session.log("Pushing the new tag")
    create_tag(version)
    notes = extract_changelog_notes(project_directory)
    create_github_release(version, notes)
