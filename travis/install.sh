#!/bin/bash
# install step in travis, but split by OS, os name is passed as first argument

# Common python requirements for all OSs
pip3 install -U pip
pip3 install -U pip setuptools pyqt5 PyInstaller requests pyqt5-sip sip 

if [ $1 = 'linux' ]; then
    # linux
    # no particular action needed
fi


if [ $1 = 'osx' ]; then
    # macos
    # no particular action needed
fi


if [ $1 = 'windows' ]; then
    # windows

    # compression tool for the portable app
    sudo apt install -y p7zip-full

    # pull the docker for windows
    docker pull cdrx/pyinstaller-windows
fi
