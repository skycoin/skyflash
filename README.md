# GUI tool to flash Skybian for Skyminer on SD card images of any kind

[![Build Status](https://travis-ci.com/skycoin/skyflash.svg?branch=master)](https://travis-ci.com/skycoin/skyflash)

With this tool you will download, configure, create and flash the default [skybian](https://github.com/simelo/skybian) image to your custom environment.

The resulting images will only run on the official skyminer hardware, the one based on Orange Pi Prime SBC.

## Skyflash

The preferred method to configure & flash the official [skybian](https://github.com/simelo/skybian) images is by using this tool

### Installing or upgrading

The Skyflash tool is a standalone app _(often called a "portable app")_, so you just download the app and run it. To get the latest version just go to the [Releases](https://github.com/skycoin/skyflash/releases) link on this page and grab the file matching to your OS.

If you has an old version already, just erase the old one and use the new one.

### Usage

To see more detailed instructions on how to use the Skyflash utility please visit the [User's Manual](USER_MANUAL.md)

## Developers & testers

If you are eager to build it yourself take into account that the base OS for dev is Ubuntu 18.04 LTS, but most of it works on OSX also if you tweak some items _(see notes below)_

The project use the GNU Make to test and build so you can ask for help like this `make help`:

```
$ make help
deps                           Install all the needed deps to build it in Ubuntu 18.04 LTS and alike
deps-windows                   Installs a docker image to build the windows .exe from inside linux
init                           Initial cleanup, erase even the final app dir
clean                          Clean the environment to have a fresh start
build                          Build the pip compatible install file
install                        Install the built pip file
win-flasher                    Create the flasher tool for windows (for travis only)
win-flasher-dev                Create the flasher tool for windows (no internet needed if you run "make deps-windows" already)
win                            Create a windows static app (for travis only)
win-dev                        Create a windows static app using local dev tools (no internet needed if you run "make deps-windows" already)
posix-streamer                 Create the linux/macos streamer to help with the flashing
linux-static                   Create a linux amd64 compatible static (portable) app
macos-app                      Create the macos standalone app
```

As you can see the options are self explanatory, just a few must know notes:

* Option starting with `deps` works only on Linux, on OSX you will need to install a few packages to get the environment ready to work:
  * xcode, brew, python3, pyqt5 & pyinstaller
* Use the `init` option to deep clean the working environment, this **will also erase** the pre-built apps.
* Use the `clean` option to soft clean the working environment, this **will not erase** the pre-built apps in the final folder.
* Options ending on `-dev` are meant to be used on linux local environments and will not pull any data from the internet if you run the `deps` & `deps-windows` before while connected to the internet.
* Option `deps-windows` installs docker for your distribution, this target is meant to build the needed toolchain in linux to build the windows app and has a trick:
  * If you don't have docker installed already you must run it, reboot or logout/login and run it again to finish the install.
* Once you run any of the release related options _(win-dev, linux-static, macos-app)_ your app will be sitting on a folder named `final`

### Releases files deploys to Github

If you plan to work on the project or just generate your own binaries using travis deploy mechanism you need to follow a few steps to do so.

0. Clone the repository in a personal or organizational repository (default develop one is at [Simelo organization in Github](https://github.com/simelo/skyflash)) and check travis has take over it and is building it on simple commits from your side.
0. Create a [Personal Access Token](https://github.com/settings/tokens) in your Github repository to allow the deploy action on release conditions, copy the token value to the clipboard.
0. Go to your travis builds for this repository and look for the settings, set the token generated as a environment variable named OAUTH

With this settings in place, you can push to both local and official repository with no fuzz

### Releases

To do a release you must follow these steps:

0. Clone the repository develop branch in a personal or organizational repository (default develop one is at [Simelo organization in Github](https://github.com/simelo/skyflash)) follow the above section to configure your repository to produce releases on your repository
0. Check if there are commits on the skycoin/master that must be applied to your develop branch (hot fixes or security ones), apply them and fix any merge issues
0. Create a release-v#.#.# branch in your repository from the develop branch, this will be the release playground, the numbers are the next logical release, see [CHANGELOG](CHANGELOG.md) file to see what's next
0. Check any pending issues in order to close them if possible on this release cycle (use local branches and at the end mix them with develop)
0. From this point forward work on the release-v#.#.# branch
0. Update the new version number in the `setup.py`, `skyflash/data/skyflash.qml` & `skyflash/utils.py` files
0. Update the `CHANGELOG.md` file with any needed info and move the `Unreleased` part to the new release version
0. Review & update the `README.md` file for any needed updates or changes that need attention in the front page
0. Push changes to your release-v#.#.# brach and wait for travis to validate all the changes
0. Tag the actual point as `Skyflash_v#.#.#-rc` and push this tag to your repository
0. On success, check the draft release is published on the repository, download the releases files and test them
0. If problems are found with raise issues where needed (skyflash/skybian) and fix them before continue with the next step
0. After all problems are solved and work as expected update the `version.txt` file with the version number, like this: v0.0.4
0. Remove the local & remote tag in created in the previous steps
0. Raise a PR against master branch in the skycoin repository, solve any issues and merge it (or wait for a privileged user to do it)
0. After solving the issues and travis validation of them, tag the actual point with the version number you wrote on the version.txt and push it
0. Waith for deploy to finish, go to Github and edit & comment the release with the changes in CHANGELOG.md that match this release, change status from Draft to Official release
0. Merge master into develop
0. Check if there is needed to raise issues & PR on the following repositories:

    * [Skybian](https://github.com/skycoin/skybian): if needed.
    * [Skycoin](https://github.com/skycoin/skycoin): mentions in it's README.md and elsewhere if applicable
    * [Skywire](https://github.com/skycoin/skywire): to note the new release and the use of skyflash
