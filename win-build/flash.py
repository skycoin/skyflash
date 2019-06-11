#!/usr/bin/env python3

# argument parser
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("file", help="The full path to the file you want to flash")
parser.add_argument("drive", help="The drive name you will to write to, like F: (case is not relevant)")
parser.add_argument("logfile", help="The file to log the activity")
args = parser.parse_args()

# advice
print("Flashing {} to drive {}".format(args.file, args.drive))

import sys
import os
import subprocess
import re
import csv

# regular expresions used below, precompiled here.
red = re.compile('Disk \#\d\, Partition \#\d')
rel = re.compile(' [A-Z]: ')

if 'nt' in os.name:
    import win32file
    import wmi

    # some aliases
    CreateFile = win32file.CreateFile
    CloseHandle = win32file.CloseHandle
    DeviceIoControl = win32file.DeviceIoControl
    ReadFile  = win32file.ReadFile
    WriteFile = win32file.WriteFile
    w32GenericRead = win32file.GENERIC_READ
    # w32FileShareRead = win32file.FILE_SHARE_READ
    w32OpenExisting = win32file.OPEN_EXISTING
else:
    print("This script is not intended for this OS")
    sys.exit()

def lockWinDevice(physicalDevice, volumeGUID):

    # The following enum/macros values were extracted from the winapi
    '''
    FILE_READ_DATA: 1
    FILE_WRITE_DATA: 2
    FILE_SHARE_READ: 1
    FILE_SHARE_WRITE: 2
    OPEN_EXISTING: 3
    INVALID_HANDLE_VALUE: -1
    FSCTL_LOCK_VOLUME: 589848
    FSCTL_DISMOUNT_VOLUME: 589856
    FORMAT_MESSAGE_FROM_SYSTEM: 4096
    MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT): 1024
    '''

    # a single devoice can have multiple drives opened, dismount it all
    hVolumes = []
    for vguid in volumeGUID:   
        # Open the volume
        hVolume = CreateFile(vguid, 1|2, 1|2, None, 3, 0, None)
        # Lock the volume
        DeviceIoControl(hVolume, 589848, None, None, None)
        # Dismount the volume
        DeviceIoControl(hVolume, 589856, None, None, None)
        # append the hvolume to the array
        hVolumes.append(hVolume)


    # the device is unique: Open the device
    hDevice = CreateFile(physicalDevice, 1|2, 1|2, None, 3, 0, None)
    # Lock the device
    DeviceIoControl(hDevice, 589848, None, None, None)
    # Dismount the device
    DeviceIoControl(hDevice, 589856, None, None, None)

    return hDevice, hVolumes

def windowsDevices():
    '''This one is to get all the info about windows removable devices in
    a big array, the format is as follows:

    [
        ['\\\\.\\PHYSICALDRIVE1', 'Mass Storage Device USB Device', '8052549120',
            [('F:\\', 'MSDOS', '\\\\?\\Volume{23e2ba26-8a62-11e9-afa4-080027673c27}\\')]
        ],
        ['\\\\.\\PHYSICALDRIVE2', 'Verbatim STORE N GO USB Device', '7739988480',
            [('G:\\', 'PAVEL', '\\\\?\\Volume{23e2ba2b-8a62-11e9-afa4-080027673c27}\\')],
            [('H:\\', 'RAPUT', '\\\\?\\Volume{23e2bcfb-8112-11e9-afa4-080276524590}\\')]
        ]
    ]

    '''

    c = wmi.WMI ()
    data = []

    for physical_disk in c.Win32_DiskDrive():
        if 7 in physical_disk.Capabilities:
            # is a removable media
            phy = physical_disk.DeviceID
            size = int(physical_disk.Size)
            desc = physical_disk.Caption
            drives = []
            for partition in physical_disk.associators ("Win32_DiskDriveToDiskPartition"):
                for logical_disk in partition.associators ("Win32_LogicalDiskToPartition"):
                    name = logical_disk.Name + "\\"
                    label = logical_disk.VolumeName
                    guid = win32file.GetVolumeNameForVolumeMountPoint(name)
                    drives.append((name, label, guid))

            data.append([phy, desc, size, drives])

    return data

def getphyguid(letter, phydata):
    '''Get the phy and guids of the drive that has the drive letter you passed'''

    if not "\\" in letter:
        letter = letter + "\\"

    for phyd in phydata:
        phy = phyd[0]
        size = int(phyd[2])
        guids = []
        isit = False
        for d in phyd[3]:
            guids.append(d[2])
            if d[0].lower() == letter.lower():
                isit = True
        
        if isit:
            return (phy, guids, size)

    return (False, False, False)


# main action goes here
image = args.file
fsize = 0
logfile = args.logfile

# get the removable drive data
data = windowsDevices()

# test if the file exist
try:
    fsize = os.path.getsize(image)
except FileNotFoundError:
    print("ERROR: File '{}' not found, please check that.".format(args.file))
    sys.exit()

# test if drive exist
# pick the phy & guids os the partitions useds
(physicalDevice, volumeGUID, dsize) = getphyguid(args.drive, data)
if physicalDevice == False:
    print("ERROR: Can't find the specified drive '{}', please check that.".format(args.drive))
    sys.exit()

# open the logfile
lf = open(logfile, mode='wt', buffering=1)

# check sizes mismatch
if fsize > dsize:
    print("ERROR: File '{}' is bigger than drive {}, aborting.".format(args.file, args.drive))
    sys.exit()

# Receive the paths to the physical device device and logical volume and return a handler to each one
try:
    hDevice, hVolumes = lockWinDevice(physicalDevice, volumeGUID)
except:
    print("ERROR: You have not proper privileges to do the operation requested. Aborting...")
    sys.exit()

# Open the Skybian file using a PyHANDLE (a wrapper to a standard Win32 HANDLE)
inputFileHandle = CreateFile(image, w32GenericRead, 0, None, w32OpenExisting, 0, None)

# windows needs a write chunk to be multiple of the sector size, aka 512 bytes
sectorSize = 512
portionSize = sectorSize * 1000 # 1/2 MB chunks
actualPosition = 0

# build node loop
while actualPosition < fsize:
    errorCode, data = ReadFile(inputFileHandle, portionSize)

    # returned error code
    if errorCode != 0: 
        print("ERROR: Read from image file failed!")
        sys.exit()
    
    # avoid writes with no sectorsize length
    if  len(data) != portionSize:
        # final part, fill with zeroes until 512 multiple
        diff = len(data) % sectorSize
        data += bytearray(sectorSize - diff)
    
    # actual write
    errorCode, ws = WriteFile(hDevice, data)

    # returned error code and data size
    if errorCode != 0: 
        print("ERROR: Write to device failed!")
        sys.exit()
    
    # check writted data length
    if ws != len(data):
        print("ERROR: Write data != from read data!")
        sys.exit()
    
    # progress and cycle update
    actualPosition += portionSize
    per = actualPosition / fsize
    if per > 100:
        per = 100.0

    lf.write("{:.1%}\n".format(per))

# close input and output file handles
CloseHandle(inputFileHandle)
CloseHandle(hDevice)
