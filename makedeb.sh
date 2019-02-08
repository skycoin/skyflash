#!/bin/bash

# This script is part of the Skyflash build scripts.
#
# This script creates the Linux standalone executable and pack it
# on a deb file ready to distribute for debian and it's flavours

# First step is to create the standalone executable via pyinstaller
rm -rdf dist
rm -rdf build
rm -rdf __cache__
pyinstaller --add-data "skyflash.qml:skyflash.qml" \
    --clean \
    -F \
    skyflash.py

# some variables
VER=0.0.3
PKG=skyflash
DEBNAME="$PKG"_"$VER"_amd64.deb

# remove final file
rm $DEBNAME &> /dev/null

# Create the deb folder structure locally
mkdir -p $PKG/usr/bin
mkdir -p $PKG/usr/share/applications/
mkdir -p $PKG/usr/share/skyflash/
mkdir -p $PKG/DEBIAN
cp dist/skyflash $PKG/usr/bin/
cp skyflash-cli $PKG/usr/bin/
cp skyflash.qml $PKG/usr/share/skyflash/
cp deb/skyflash.desktop $PKG/usr/share/applications/
cp deb/skyflash.png $PKG/usr/share/skyflash/

# fix permissions
# chown -R root:root $PKG/
chmod +x $PKG/usr/bin/skyflash*

# dynamic values & other tricks
size=`du -s $PKG/ | awk '{print $1}'`

cat << EOF > $PKG/DEBIAN/control
Package: $PKG
Version: $VER
Maintainer: Pavel Milanes <pavelmc@gmail.com>
Architecture: amd64
Section: main
Priority: optional
Depends: libc6 (>= 2.25), pv (>=1.5)
Installed-Size: $size
Description: A tool to customise your Skycoin Skyminer OS images
 Skyflash is the tool used to customise Skybian, the Skycoin Skyminers official OS.
 .
 Within this package we have skyflash and skyflash-cli
 .
 skyflash is a GUI interface written in Python3 + PyQT5 + QML and packaged with pyinstaller as a standalone executable elf file for the linux desktop.
 .
 skyflash-cli is a linux bash script that performs the same task but in command line. 
EOF

# build the final deb package
dpkg-deb --build --root-owner-group "$PKG" "$DEBNAME"
