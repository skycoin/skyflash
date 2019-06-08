#!/bin/bash
# build to release step in travis, but split by OS, os name is passed as first argument

if [ $1 = 'linux' ]; then
    # linux
    make deb
    make linux-static
fi


if [ $1 = 'osx' ]; then
    # macos
    make macos-app
fi


if [ $1 = 'windows' ]; then
    # windows
    make win-static
fi
