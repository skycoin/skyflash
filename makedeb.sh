#!/bin/bash

# This script is part of the Skyflash build scripts.
#
# This script creates the Linux standalone executable and pack it
# on a deb file ready to distribute


# First step is to create the standalone executable
# rm -rdf dist
# rm -rdf build
# rm -rdf __cache__
# pyinstaller --add-data "skyflash.qml:skyflash.qml" \
#     --clean \
#     -F \
#     skyflash.py
# exec is in ./dist/skyflash

# Create the deb folder structure locally
mkdir -p skyflash/usr/local/bin
mkdir -p skyflash/DEBIAN
cp dist/skyflash skyflash/usr/local/bin/
cp skyflash.qml skyflash/usr/local/bin/
cp skyflash-cli skyflash/usr/local/bin/

size=`du -s skyflash/usr/local/bin | awk '{print $1}'`

cat << EOF > skyflash/DEBIAN/control
Package: skyflash
Version: 0.0.3
Maintainer: pavelmc@gmail.com
Architecture: amd64
Section: main
Priority: optional
Depends: libc6 (>= 2.25), pv (>=1.5)
Installed-Size: $size
Description: A set of CLI & GUI tools to create your custom Skyminer OS images
EOF

# build the final deb package
dpkg-deb --build --root-owner-group skyflash skyflash_0.0.3_amd64.deb

