#!/bin/bash
# install step in travis, but split by OS

# WARNING
# 'python' points to Python 2.7 on macOS but points to Python 3.7 on Linux and Windows
# 'python3' is a 'command not found' error on Windows but 'py' works on Windows only

if [ $TRAVIS_OS_NAME = 'linux' ]; then
    # linux
    sudo apt-get update -q
    sudo apt install -y python3 python3-all python3-pip python3-pyqt5 python3-pyqt5.qtquick qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-layouts qml-module-qtquick-extras qml-module-qtquick-dialogs qml-module-qtquick-controls qml-module-qt-labs-folderlistmodel qml-module-qt-labs-settings fakeroot python3-stdeb p7zip-full make
fi


if [ $TRAVIS_OS_NAME = 'osx' ]; then
    # macos
    pip install --upgrade pip  # all three OSes agree about 'pip3'
fi


if [ $TRAVIS_OS_NAME = 'windows' ]; then
    # windows
    pip3 install --upgrade pip  # all three OSes agree about 'pip3'
    choco install make
    choco install sudo
    ls -lh
    echo "Working path is:"
    pwd
fi

# all 3 oses are agree about pip3, so direct here: install pyinstaller & pyqt5
pip3 install setuptools pyqt5 PyInstaller