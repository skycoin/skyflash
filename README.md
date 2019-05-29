# skyflash is a tool to configure & flash skybian base images for the official skycoin skyminers

With this tool you will be able configure the default [skybian](https://github.com/simelo/skybian) image to your custom environment and create the needed images for it.

The resulting images will only run on the official skyminer hardware, aka: Orange Pi Prime SBC, for now.

The tool has two variants:

* A general use GUI tool (skyflash) that works on Linux & Windows _(Mac support is a work in progress)_
* A Linux only CLI tool (skyflash-cli) **_for developers and advanced users only in Linux, see below_**.

## Skyflash GUI tool

The preferred method to configure & flash skybian images is by using this GUI tool

### Installing

To install this tool, go to the [Releases](https://github.com/skycoin/skyflash/releases) link on this page and grab the file corresponding file to your OS, use the following table to figure it out:

| Operating System | You must download the one... |
|:----------------:|:--------------------------------:|
| Windows app| **Skyflash.exe** |
| Linux | **python3-skyflash_[version]_all.deb** |
| Linux static app| **skyflash-gui_linux64-static.gz** |
| MacOS | TBD |
| Python3 pkg | **skyflash-[version].tar.gz**  _(advanced users)_| 

Installing it and running is done by the default OS way, google is your friend on this.

### Usage

To see more detailed instructions on how to use the Skyflash GUI utility please visit the [User's Manual](USER_MANUAL.md)

## skyflash-cli tool (developer)

The CLI interface for linux developers has [help & usage guide with examples](skyflash-cli_MANUAL.md) if you are interested on it

## Releases

To do a release you must follow these steps:

0. Check if there are commits on the master branch that must be applied to develop (hot fixes or security ones), apply them and fix any merge issues.
0. On develop branch, check any pending issues in order to close them if possible on this release and close them is possible.
0. Check the latest release of Skybian and if the URL of the latest image is different rise a issue and solve it by the default way.
0. Merge the develop branch into the release one and fix any conflicts if any.
0. Update the new version number in the `setup.py` & `skyflash/data/skyflash.qml` files.
0. Update the `CHANGELOG.md` file with any needed info and move the `Unreleased` part to the new release version.
0. Review & update the `README.md` file for any needed updates or changes that need attention in the front page.
0. Wait for travis to validate all the changes.
0. On success, check the draft release is published on the repository, improve it and keep it as a draft.
0. Download the releases files and test them.
0. If problems are found with raise issues where needed (skyflash/skybian) and fix them before continue with the next step.
0. Download the releases files after the fix in the previous step (if needed) and test them.
0. Fix any issues if found (work in the release branch)
0. After all problems are solved and work as expected, tag it as `Skyflash-X.Y.Z` & raise a PR against master branch, solve any issues and merge it.
0. Wait for travis completion and check the release files are published on the Github repository under releases.
0. Edit & comment the release with the changes in CHANGELOG.md that match this release, change status from Draft to Official release.
0. Merge master into develop.
0. Check if there is needed to raise issues & PR on the following repositories:

    * [Skybian](https://github.com/skycoin/skybian): if needed.
    * [Skycoin](https://github.com/skycoin/skycoin): mentions in it's README.md and elsewhere if applicable
    * [Skywire](https://github.com/skycoin/skywire): to note the new release and the use of skybian/skyflash