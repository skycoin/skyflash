#!/bin/bash
# install step in travis, but split by OS


# all 3 oses are agree about pip3, so direct here: install pyinstaller & pyqt5
pip3 install setuptools pyqt5 PyInstaller

if [ $TRAVIS_OS_NAME = 'linux' ]; then
    # linux
    - sudo apt-get update -q
    - sudo apt install -y python3 python3-all python3-pip python3-pyqt5 python3-pyqt5.qtquick qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-layouts qml-module-qtquick-extras qml-module-qtquick-dialogs qml-module-qtquick-controls qml-module-qt-labs-folderlistmodel qml-module-qt-labs-settings fakeroot python3-stdeb p7zip-full make
fi


if [ $TRAVIS_OS_NAME = 'osx' ]; then
    # macos
    - echo "No particular depencency Yet"
fi


if [ $TRAVIS_OS_NAME = 'windows' ]; then
    # windows
    # TODO 7z utility
    - echo "No particular depencency Yet"
fi
