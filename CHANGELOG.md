# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Syntax:

```text
## [version] - YYYY-MM-DD
### Added/Removed/Changed/Deprecated/Fixed/Security
```

## [Latest Changes]

## [0.3.0] - 2022-03-16

 - Create workflow to deploy to pypi
 - Fix linting errors
 - Fix replacing versions inside single quotes
 - Add loguru logging
 - Add badges to README
 - Fix incorrect test
 - Update development dependencies and commands
 - Add overview to docs
 - Bump version to v0.2.0
 - Fix git and github commands to use text
 - Ensure repository ends with a slash
 - Add commit messages to changelog if empty
 - Use first commit as starting version if tag doesn't exist
 - Create basic cli entrypoint
 - Improve change type guesses
 - Basic guess of version to bump using commmit msgs
 - Switch to using `subprocess.run` instead of `subprocess.call`.
 - Refactor project-specific functions into class
 - Parse recent changes and create github release
 - Cleanup files
 - Refactor bump logic into package
 - Fix paths
 - Initial commit
 - Basic release process using `nox`.

## [0.2.1] - 2022-03-16

### Added
- Logging using [loguru](https://github.com/Delgan/loguru)

### Fixed
- Bug where versions inside single-quotes weren't being replaced.

## [0.2.0] - 2022-03-15

- Initial project setup


[Latest Changes]: https://github.com/lucasmelin/molting/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/lucasmelin/molting/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/lucasmelin/molting/compare/v0.2.0...v0.2.1
