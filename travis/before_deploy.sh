#!/bin/bash
# build to release step in travis, but split by OS
#
# - OS name is passed as first argument
# - Version is passed as second

if [ ${1} = 'linux' ]; then
    # linux
    make linux-static

    # rename the final app
    mv final/skyflash.gz final/Skyflash_${2}_${1}_amd64.gz
fi


if [ ${1} = 'osx' ]; then
    # macos
    make macos-app

    # rename the final app
    mv final/skyflash.tgz final/Skyflash_${2}_${1}.tgz
fi


if [ ${1} = 'windows' ]; then
    # windows
    make win

    # rename the final app
    mv final/skyflash.exe final/Skyflash_${2}_${1}_amd64.exe
fi
