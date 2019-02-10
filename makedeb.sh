#!/bin/bash

# This script is part of the Skyflash build scripts.
#
# This script creates the Linux standalone executable and pack it
# on a deb file ready to distribute for debian and it's flavours

# some variables
VER=0.0.3
PKG=skyflash
DEBNAME="$PKG"_"$VER"_amd64.deb

# remove trash to start fresh
rm -rdf $PKG &> /dev/null
rm -rf *.deb &> /dev/null

# Create the deb folder structure locally
mkdir -p $PKG/opt/$PKG
mkdir -p $PKG/usr/share/applications
mkdir -p $PKG/usr/bin
mkdir -p $PKG/DEBIAN
cp skyflash.py $PKG/opt/$PKG/
cp skyflash.qml $PKG/opt/$PKG/
cp skyflash.png $PKG/opt/$PKG/
cp README.md $PKG/opt/$PKG/
cp skyflash-cli $PKG/usr/bin/
cp deb/skyflash $PKG/usr/bin/
cp deb/skyflash.desktop $PKG/usr/share/applications/

# fix permissions
# chown -R root:root $PKG/
chmod +x $PKG/usr/bin/skyflash-cli
chmod +x $PKG/usr/bin/skyflash

# capture the aproximate pkg size
SIZE=`du -s $PKG/ | awk '{print $1}'`

# dynamic values & other tricks over the control file
cat ./deb/control | \
    sed s/"PKG"/"$PKG"/ | \
    sed s/"VER"/"$VER"/ | \
    sed s/"SIZE"/"$SIZE"/ > $PKG/DEBIAN/control

# build the final deb package
dpkg-deb --build --root-owner-group "$PKG" "$DEBNAME"
