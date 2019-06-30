#!/bin/bash
# build to release step in travis, but split by OS, os name is passed as first argument

if [ $1 = 'linux' ]; then
    # linux
    make linux-static
fi


if [ $1 = 'osx' ]; then
    # macos
    make macos-app
fi


if [ $1 = 'windows' ]; then
    # build the docker machine in-situ
    cd docker/win64py3/
    docker build -t "pyinstaller-win64py3:skyflash" ./

    # exit the docker directory
    cd ../../

    # windows
    make win-dev
fi
