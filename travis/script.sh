#!/bin/bash

# Testing of the build

# for everyone
make init

# build & install, but windows need python only
if [ $TRAVIS_OS_NAME = 'windows' ]; then
    # windows
    sudo python setup.py install
else
    make install
fi