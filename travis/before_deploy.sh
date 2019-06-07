#!/bin/bash

# before deploy commands, create the release files

if [ $TRAVIS_OS_NAME = 'linux' ]; then
    # linux
    make deb
    make linux-static
fi


if [ $TRAVIS_OS_NAME = 'osx' ]; then
    # macos
    make macos-app
fi


if [ $TRAVIS_OS_NAME = 'windows' ]; then
    # windows
    make win-travis
fi
