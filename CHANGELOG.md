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

## v0.0.4 - 2019-07-12

### Added

- Setuptools compatibility (structure and code changed)
- Travis yml file for CI/CD
- Developers now can create a local Docker image to generate the Windows .exe release file from a linux host
- Full flashing support in Windows & Linux
- New flashing paradigm in the UI, to help the user and allow for repeated flashing
- Full flashing support in macos OSX
- Full generation of release files via Travis
- Make now can take care of dependencies in linux for the devs
- Doc update with latest changes
- UI now shows the name and version of the base image being processed.
- Skyflash now checks for new versions on startup, if found will warn the user and open a web browser with indications to the user...
- Skyflash now detects the latest stable version of Skybian (from internet) and use that for the download... if it can detect it, just use the hardcoded one.
- Added a new dependency for python3: request module, drop your local created docker image and re-create it, see 'make help'

### Changed

- Structure changed to support python3 setutools
- Versioning for Skyflash will match the Skywire ones, starting with 0.0.4
- Separated user manual for the CLI utility
- README and MANUALS updated to reflect recent changes
- Makefile options changed
- Posix OS (Linux/OSX) now uses a own streamer app to feed dd fon the flash process
- Windows uses a own flasher app (flash.exe)
- The docker image in the dev stage that was named "pyinstaller-win64py3:pyqt_winapi" and then renamed to pyinstaller-win64py3:skyflash please remove the old and run `make deps-windows` to re-create the new docker image.
- We will not longer release a .deb file for installation, use the linux static app instead.
- The network config now has a natural view on the IPs, no more spaces in the IPs
- The internal validation mechanism for the IPs and DNS entries was rebuilt almost from scratch
- Dev docker image updated, please run `make deps-windows` to erase your old one and to re-create the updated one
- Change in Python & PyQt5 version, now we use Python v3.6 and PyQt5 v 5.13
