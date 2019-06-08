#!/bin/bash
# install step in travis, but split by OS, os name is passed as first argument

# WARNING
# 'python' points to Python 2.7 on macOS but points to Python 3.7 on Linux and Windows
# 'python3' is a 'command not found' error on Windows but 'py' works on Windows only

if [ $1 = 'linux' ]; then
    # linux
    sudo apt-get update -q
    sudo apt install -y python3 python3-all python3-pip python3-pyqt5 python3-pyqt5.qtquick qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-layouts qml-module-qtquick-extras qml-module-qtquick-dialogs qml-module-qtquick-controls qml-module-qt-labs-folderlistmodel qml-module-qt-labs-settings fakeroot python3-stdeb p7zip-full make
    pip3 install setuptools pyqt5 PyInstaller
fi


if [ $1 = 'osx' ]; then
    # macos
    pip install --upgrade pip
    pip3 install setuptools pyqt5 PyInstaller
fi


if [ $1 = 'windows' ]; then
    # windows
    sudo apt-get update -q
    sudo apt install -y python3 python3-all python3-pip python3-pyqt5 python3-pyqt5.qtquick qml-module-qtquick2 qml-module-qtquick-window2 qml-module-qtquick-layouts qml-module-qtquick-extras qml-module-qtquick-dialogs qml-module-qtquick-controls qml-module-qt-labs-folderlistmodel qml-module-qt-labs-settings fakeroot python3-stdeb p7zip-full make
    pip3 install setuptools pyqt5
    # pull the docker for windows
    docker pull cdrx/pyinstaller-windows
fi
