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

## v0.0.4-beta - 2019-06-08

### Added

- Setuptools compatibility (structure and code changed)
- Travis yml file for CI/CD
- Developers now can create a local Docker image to generate the Windows .exe release file
- Full flashing support in Windows & Linux
- New flashing paradigm in the UI, to help the user and
- Full flashing support in macos OSX
- Full generation of release files via Travis
- Make now can take care of dependencies in linux
- Doc update with latest changes
- UI now shows the name and version of the base image being processed.

### Changed

- Structure changed to support python3 setutools
- Versioning for Skyflash will match the Skywire ones, starting with 0.0.4
- Separated user manual for the CLI utility
- README and MANUALS updated to reflect recent changes
- Makefile options changed
- Posix OS (Linux/OSX) now uses a own streamer app to feed dd fon the flash process
- Windows uses a own flasher app (flash)
- The docker image in the dev stage that was named "pyinstaller-win64py3:pyqt_winapi" and then renamed to pyinstaller-win64py3:skyflash please remove the old and run `make deps-windows` to re-create the new docker image.
- We will not longer release a .deb file for installation, use the linux static app instead.
