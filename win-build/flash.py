#!/usr/bin/env python3

# argument parser
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("file", help="The full path to the file you want to flash")
parser.add_argument("drive", help="The drive name you will to write to, like F: (case is not relevant)")
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
    import ctypes
    import win32api
    import win32file

    # some aliases
    CreateFile = win32file.CreateFile
    CloseHandle = win32file.CloseHandle
    DeviceIoControl = win32file.DeviceIoControl
    #getLogicalDrives = win32file.GetLogicalDrives
    getLogicalDrives = ctypes.windll.kernel32.GetLogicalDrives
    #getVolumeInformation = win32api.GetVolumeInformation
    getVolumeInformation = ctypes.windll.kernel32.GetVolumeInformationW
    ReadFile  = win32file.ReadFile
    WriteFile = win32file.WriteFile
    createUnicodeBuffer = ctypes.create_unicode_buffer
    sizeof = ctypes.sizeof
    w32GenericRead = win32file.GENERIC_READ
    w32FileShareRead = win32file.FILE_SHARE_READ
    w32OpenExisting = win32file.OPEN_EXISTING
else:
    print("This script is not intended for this OS")
    sys.exit()

def sysexec(cmd):
    '''
    Execute a command in the console of the base os, this one is intended
    for windows only.

    It parses the output into a list (by line endings) and cleans empty ones
    '''

    l = subprocess.check_output(cmd, shell=True)
    l = l.decode(encoding='oem').splitlines()

    # cleans empty lines
    for i in l:
        if i == '': l.remove('')

    return l

def getLetter(logicaldrive):
    '''Windows Only:
    It get the device ID in this format: "Disk #0, Partition #0"
    and answer back with an drive letter matching or a empty str
    if not mounted/used
    '''

    l = sysexec("wmic partition where (DeviceID='{}') assoc /assocclass:Win32_LogicalDiskToPartition".format(logicaldrive))

    r = []
    # filter for " G: "
    # if not matching need to return ""

    for e in l:
        fe = rel.findall(e)
        for ee in fe:
            nee = ee.strip()
            if not nee in r:
                r.append(nee)

    if len(r) > 0:
        # DEBUG
        d = r[0].strip()
        return d
    else:
        return ''

def getLogicalDrive(phydrive, letter):
    '''Windows only
    Get the physical drive (\\\\.\\PHYSICALDRIVE0) name and
    return the logical volumes in a list like this
        Disk #0, Partition #0
        Disk #0, Partition #1
        etc...

    associated with it
    '''

    # scape the \'s in the name of the device
    phydrive = phydrive.replace('\\\\.\\', '\\\\\\\\.\\\\')
    l = sysexec("wmic DiskDrive where \"DeviceID='" + "{}".format(phydrive) + "'\" Assoc /assocclass:Win32_DiskDriveToDiskPartition")

    record = []
    data = []

    # the list has many times the same info, pick unique names
    # dive into results
    for element in l:
        # matching it via regular expressions
        for logVol in red.findall(element):
            # already present?
            if not logVol in record:
                # just add the one with the drive letter name as the passed one
                # get the drive letter associated with the logDrive
                l = getLetter(logVol)
                if l.lower() == letter.lower():
                    record.append(logVol)
                    # get the guid
                    g = getWinGUID(l)
                    # adding the info to the return list
                    data.append([logVol, l, getLabel(l), g])

    return data

def getLabel(d):
    '''Windows Only:
    From a drive letter, get the label if proceed
    '''

    name_buffer = createUnicodeBuffer(1024)
    filesystem_buffer = createUnicodeBuffer(1024)
    volume_name = ""
    drive = u"{}/".format(d)
    # drive = drive.encode("ascii")
    error = getVolumeInformation(ctypes.c_wchar_p(drive), name_buffer,
            ctypes.sizeof(name_buffer), None, None, None,
            filesystem_buffer, ctypes.sizeof(filesystem_buffer))

    if error != 0:
        volume_name = name_buffer.value

    if not volume_name:
        volume_name = "[No Label]"

    return volume_name

def getWinGUID(drive):
    '''Windows Only
    Get the capacity, deviceId, driveletter for all storage devices on the machine
    then filter by drive and & return false or the string of the guid

    Tip: if ithas no letter windows can't handle it, so no worry
    '''

    l= sysexec("wmic volume get Capacity,DeviceID,DriveLetter /format:csv")
    listd = csv.reader(l)
    header = next(listd)

    # extracted fields
    sizeh = header.index("Capacity")
    guidh = header.index("DeviceID")
    letter = header.index("DriveLetter")

    guid = False
    for r in listd:
        if len(r) == 0:
            continue

        # if no drive letter match the size
        if len(r[letter]) > 0 and r[letter] == drive:
            guid = r[guidh]

    return guid

def getPHYDrives(letter):
    '''
    List all physical drives, filter for the ones with the removable
    media flag (most likely card readers & USB thumb drives) and
    retrieve the logical drive name and it's letter if proceed

    Returns an array with physical & logical names for drives, it's
    associated letter, size and the interface type.
    '''

    l = sysexec("wmic diskdrive list full /format:csv")

    # get the headers
    listd = csv.reader(l)
    header = next(listd)

    # extracted fields
    capa = header.index("Capabilities") # {3;4;7} we are looking for '7' aka removable media
    phydrive = header.index("DeviceID")
    interface = header.index("InterfaceType")
    descDirty = header.index("PNPDeviceID")
    size = header.index("Size")

    # output dict
    d = dict()

    for r in listd:
        if len(r) == 0:
            continue

        # check if the media is removable (cap has #7)
        capas = r[capa].strip('{}').split(';')
        if '7' in capas:
            # get logical drive data
            drive = getLogicalDrive(r[phydrive], letter)

            # just add the ones for the drive we want
            if len(drive) > 0:
                d['drives'] = drive
                d["phydrive"] = r[phydrive]
                d["interface"] = r[interface]
                d["desc"] = r[descDirty]
                d["size"] = r[size]

    # sample output & watch out: we on ly return data for the drive we are asked for
    #
    # [{'desc': 'USBSTOR\\DISK&amp;VEN_MASS&amp;PROD_STORAGE_DEVICE&amp;REV_1.00\\121220160204&amp;0',
    # 'drives': [['Disk #2, Partition #0',
    #             'H:',
    #             '[No Label]',
    #             '\\\\?\\Volume{37189f6b-5e76-11e9-a1fd-0800275fd42d}\\']],
    # 'interface': 'USB',
    # 'phydrive': '\\\\.\\PHYSICALDRIVE2',
    # 'size': '8052549120'}]

    return d

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

    # Open the device
    hDevice = CreateFile(physicalDevice, 1|2, 1|2, None, 3, 0, None)

    # Open the volume
    hVolume = CreateFile(volumeGUID, 1|2, 1|2, None, 3, 0, None)

    # Lock the volume
    DeviceIoControl(hVolume, 589848, None, None, None)

    # Dismount the volume
    DeviceIoControl(hVolume, 589856, None, None, None)

    # Lock the device
    DeviceIoControl(hDevice, 589848, None, None, None)

    # Dismount the device
    DeviceIoControl(hDevice, 589856, None, None, None)

    return hDevice, hVolume


# main action goes here
image = args.file

# test if the file exist
try:
    fsize = os.path.getsize(image)
except FileNotFoundError:
    print("ERROR: File '{}' not found, please check that.".format(args.file))
    sys.exit()

# test if drive exist
ddata = getPHYDrives(args.drive)
if len(ddata) == 0:
    print("ERROR: Can't find the specified drive '{}', please check that.".format(args.drive))
    sys.exit()

physicalDevice = ""
volumeGUID = ""

# TODO: Need windows device lock to allow raw write
desc = ddata['desc']
driv = ddata['drives'][0][3]
dsize = int(ddata['size'])
physicalDevice = str(ddata['phydrive'])
volumeGUID = str(driv[:-1])

# check sizes mismatch
if fsize > dsize:
    print("ERROR: File '{}' is bigger than drive {}, aborting.".format(args.file, args.drive))
    sys.exit()

if physicalDevice == "" or volumeGUID == "":
    print("ERROR: Cannot find the physical device path or volume GUID path. Aborting...")
    sys.exit()


# Receive the paths to the physical device device and logical volume and return a handler to each one
try:
    hDevice, hVolume = lockWinDevice(physicalDevice, volumeGUID)
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
    print("{:.2%}".format(actualPosition / fsize))

# close input and output file handles
CloseHandle(inputFileHandle)
CloseHandle(hDevice)
