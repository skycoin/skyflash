#!/bin/bash

# This script is part of the Skyflash build scripts.
#
# This script creates the Linux standalone executable and pack it
# on a deb file ready to distribute


# First step is to create the standalone executable
rm -rdf dist
rm -rdf build
rm -rdf __cache__
pyinstaller --add-data "skyflash.qml:skyflash.qml" \
    --clean \
    -F \
    skyflash.py
# exec is in ./dist/skyflash

# some variables
VER=0.0.3
PKG=skyflash

# Create the deb folder structure locally
mkdir -p $PKG/usr/local/bin
mkdir -p $PKG/usr/share/applications/
mkdir -p $PKG/usr/local/share/skybian/
mkdir -p $PKG/DEBIAN
cp dist/skyflash $PKG/usr/local/bin/
cp skyflash.qml $PKG/usr/local/bin/
cp skyflash-cli $PKG/usr/local/bin/
cp deb/skyflash.desktop $PKG/usr/share/applications/
cp deb/Skycoin.png $PKG/usr/local/share/skybian/

# dynamic values & other tricks
size=`du -s $PKG/usr/local/bin | awk '{print $1}'`

cat << EOF > $PKG/DEBIAN/control
Package: $PKG
Version: $VER
Maintainer: Pavel Milanes <pavelmc@gmail.com>
Architecture: amd64
Section: main
Priority: optional
Depends: libc6 (>= 2.25), pv (>=1.5)
Installed-Size: $size
Description: A set of CLI & GUI tools to create your custom Skyminer OS images
EOF

# build the final deb package
dpkg-deb --build --root-owner-group $PKG "$PKG"_"$VER"_amd64.deb

