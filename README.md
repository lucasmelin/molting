# 🐍🐍 molting

Automatically bump your project files to the latest version.

![PyPI](https://img.shields.io/pypi/v/molting?color=%2316a34a)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/molting?color=%230fb882)
[![CI - nox sessions](https://github.com/lucasmelin/molting/actions/workflows/ci.yaml/badge.svg)](https://github.com/lucasmelin/molting/actions/workflows/ci.yaml)

---

## Overview

Simplifies the process of creating new releases by bumping version numbers, updating release notes, and creating a GitHub release.

- **Easy to use** - Can be called without any arguments; let `molting` figure out the specifics.
- **Built for CI/CD** - Run from GitHub Actions or similar CI/CD tool to completely automate your release process.

## How it works

```mermaid
graph TD
    A[Invoke molting CLI] -->|Specify semver type| B(Calculate new version)
    A -->|Omit semver type| C(Get commit messages)
    C --> D[Guess change type]
    D --> B
    B --> G(Get changelog notes)
    G -->|Changelog notes found| E(Update version in files)
    G -->|No Changelog notes exist| J(Get commit messages)
    J -->|Write commit messages to Changelog| G
    E --> F(Create new git tag)
    F --> K(Create GitHub release with Changelog notes)
```
