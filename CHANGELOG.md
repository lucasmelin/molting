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

### Changed

- Improved how `--dry-run` is handled, as well as the log output

### Fixed

- Tightened glob parameters when searching for `__init__.py` files, so that only project-related files are returned

## [0.3.0] - 2022-03-16

### Added

- Workflow to deploy to PyPi

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
