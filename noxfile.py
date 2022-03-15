"""Nox sessions."""
import tempfile
from pathlib import Path

import nox

package = "molting"
nox.options.sessions = "lint", "safety", "tests"
locations = "src", "tests", "noxfile.py"


def install_with_constraints(session, *args, **kwargs):
    """Install packages constrained by Poetry's lock file."""
    requirements = tempfile.NamedTemporaryFile(delete=False)
    try:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--without-hashes",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        session.install(f"--constraint={requirements.name}", *args, **kwargs)
    finally:
        requirements.close()
        Path(requirements.name).unlink()


@nox.session
def black(session):
    """Run black code formatter."""
    args = session.posargs or locations
    install_with_constraints(session, "black")
    session.run("black", *args)


@nox.session
def docs(session):
    """Build the documentation."""
    install_with_constraints(session, "mkdocs-material", "mkdocstrings")
    session.run("mkdocs", "build")


@nox.session
def lint(session):
    """Lint using flake8."""
    args = session.posargs or locations
    install_with_constraints(
        session,
        "isort",
        "flake8",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-comprehensions",
        "flake8-docstrings",
        "flake8-import-order",
    )
    session.run("isort", "--check", "--diff", "--profile", "black", *args)
    session.run("flake8", *args)


@nox.session
def publish_docs(session):
    """Publish the documentation to GitHub Pages."""
    install_with_constraints(session, "mkdocs-material", "mkdocstrings")
    session.run("mkdocs", "gh-deploy")


@nox.session
def safety(session):
    """Scan dependencies for insecure packages."""
    requirements = tempfile.NamedTemporaryFile(delete=False)
    try:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--without-hashes",
            "--format=requirements.txt",
            f"--output={requirements.name}",
            external=True,
        )
        install_with_constraints(session, "safety")
        session.run("safety", "check", f"--file={requirements.name}", "--full-report")
    finally:
        requirements.close()
        Path(requirements.name).unlink()


@nox.session
def tests(session):
    """Run the test suite."""
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(
        session,
        "coverage[toml]",
        "pytest",
        "pytest-cov",
        "pytest-mock",
    )
    session.run("pytest", *args)
