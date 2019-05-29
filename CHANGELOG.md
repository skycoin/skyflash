# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!--
This is a note for developers about the recommended tags to keep track of the changes:

- Added: for new features.
- Changed: for changes in existing functionality.
- Deprecated: for soon-to-be removed features.
- Removed: for now removed features.
- Fixed: for any bug fixes.
- Security: in case of vulnerabilities.

Dates must be YEAR-MONTH-DAY
-->

## [Unreleased] - 2019-05-29

### Added

- Setuptools compatibility (structure and code changed)
- Travis yml file for CI/CD
- Developers now can create a local Docker image to generate the Windows .exe release file
- Full flashing support in Windows & Linux
- New flashing paradigm in the UI, to help the user and

### Changed

- Disabled the flash part in Mac, as this is not done yet
- Structure changed to support python3 setutools
- Versioning for Skyflash will match the Skywire ones, starting with 0.0.4
- Separated user manual for the CLI utility
- README and MANUALS updated to reflect recent changes
