import nox
import argparse
from pathlib import Path
from molting.main import Project, increase_version_number


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

    project = Project(".")
    old_version = project.get_version()

    version = increase_version_number(old_version, version_part)

    project.update_changelog(old_version, version)
    project.update_pyproject(version)
    project.update_init(version)
    session.log(f"Bumped files from {old_version!r} to {version!r}")
    session.log("Pushing the new tag")
    # create_tag(version)
    # notes = project.extract_changelog_notes()
    # create_github_release(version, notes)
