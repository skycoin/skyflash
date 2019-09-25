# part of skyflash
# misc tools used by skyflash

import sys
import os
import io
import enum
import traceback
import subprocess
import json
import ipaddress
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot

# import the windows libs only in linux
try:
    import wmi
    import win32file
except:
    if sys.platform is 'nt':
        print("Missing python3 wmi or pywin32 modules...")

# version data
actualVersion = "v0.0.5"
updateURL = "https://raw.githubusercontent.com/skycoin/skyflash/master/version.txt"
skybianVersionFile = "https://raw.githubusercontent.com/skycoin/skybian/master/version.txt"

def cleanString(data):
    '''Cleans a string from trailing or leading chars

    The list of chars is the cleanOf below, it's just a hack with strip()
    but saves you from typing boring sentences over and over'''

    cleanOf = " ,.-"

    return data.strip(cleanOf)

def splitDNS(dnsString):
    '''Split a string that can represent up to tree DNS entries
    return a list with the entries, if on error first entry is False
    and second is the reason
    '''

    # first detecting the split pattern and detecting the most likely
    data = dnsString.split(" ")
    coma = dnsString.split(",")
    if len(coma) > len(data):
        data = coma

    dns = []
    err = False
    for e in data:
        result, ip = (validIP(cleanString(e)))
        if result:
            dns.append(str(ip))
        else:
            return [False, ip]

    return dns

def shortenPath(fullpath, ccount):
    '''Shorten a passed FS path to a char count size

    If ccount is -1 then return the last part of the path
    '''

    fpath = fullpath.split(os.sep)
    fpath.reverse()
    spath = fpath[0]

    if ccount != -1:
        # cycle from back to start to fit on ccount
        for item in fpath:
            if item == fpath[0]:
                # filename
                spath = item
            else:
                # folders
                tspath = item + os.sep + spath
                if len(tspath) > ccount:
                    spath = "..." + os.sep + spath
                    break
                else:
                    spath = tspath

    # spath has the final shorted path
    return spath

def eta(secs):
    '''Format a second time span in a text human readable representation
    returned as a string, for example:

    secs < 10 seconds:  "a few seconds"
    secs > 10 seconds & < 1 minute: "{secs} seconds"
    secs > 1 minute & < 59 minutes: "{min} minutes"
    secs > 1 hour: "{} hour {} minutes"
    '''

    # vars
    mins = int(secs / 60)
    hours = int(mins / 60)
    out = ""

    if mins < 1:
        if secs < 10:
            out = "a few secs"
        else:
            out = "{} secs".format(secs)
    elif mins < 59:
        out = "{} min".format(mins)
    else:
        if hours > 1:
            out = "{} hours {} min".format(hours, int(mins % 60))
        else:
            out = "{} hour {} min".format(hours, int(mins % 60))

    return out

def speed(speed):
    '''Takes a bytes per second speeds and returns a string with a human readable
    representation of that speed, such as:

    speed < 1 KB/s: "{} b/s"
    speed > 1 KB/s & < 1 MB/s: "{} KB/s"
    speed > 1 MB/s: {} MB/s
    '''

    # vars
    k = speed / 1000
    M = k / 1000
    out = ""

    if M > 1:
        out = "{:0.1f} MB/s".format(M)
    elif k > 1:
        out = "{:0.1f} KB/s".format(k)
    else:
        out = "{} b/s".format(int(speed))

    return out

def size(size):
    '''Takes a byte size and return it as a human readable string,
    such as this:

    size < 1 KB: "{} bytes"
    size > 1 KB & < 1 MB:  "{0.3f} KB"
    size > 1 MB: "{0.3f} MB"
    '''

    # vars
    k = size / 1000
    M = k / 1000
    out = ""

    if M > 1:
        out = "{:0.3f} MB".format(M)
    elif k > 1:
        out = "{:0.3f} KB".format(k)
    else:
        out = "{} bytes".format(int(size))

    return out

def validIP(iip):
    '''Takes a string of a IP and return a tuple:
    true/false and a reason if false

    It uses ipaddress stock module, and the error is returned as the default comment 
    '''

    try:
        ip = ipaddress.IPv4Address(iip)
        return (True, ip)
    except ValueError as messg:
        return (False, str(messg))

def getLinuxPath(soft):
    '''Make use of getDataFromCLI
       Return False if the soft is not in the system or the path string if true'''

    output = getDataFromCLI("which {}".format(soft))

    if not output:
        return output
    else:
        return output.strip("\n")

def getDataFromCLI(cmd):
    '''Returns the data from a cmd line to run on linux
       if data is empty returns false
    '''

    try:
        output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        return False

    if output == '':
        output = False

    return bytes(output).decode()

def setPath(dir):
    '''Pick the correct path for the current OS and create it if not there
    This is the path in with we will download, extract, create, etc.

    dir is the app name folder "Skyflash" by default
    '''

    # default path for the user
    workpath = os.path.expanduser('~')

    # where in the user's folder I need to put the  skybian folder:
    # linux and macos right in the home folder, windows on the document folder
    if sys.platform in ["win32", "cygwin"]:
        # windows
        # path has the c:\Users\[username] so we need to add the Documents folder
        # Windows has a trick for other langs beside English: Documents is the real
        # folder and other lang folders just point to that
        workpath = os.path.join(workpath, "Documents")

    # now adding the app dir
    workpath = os.path.join(workpath, dir)

    # test if the folder is already there
    if not os.path.isdir(workpath):
        # creating the folder, or not if created
        os.makedirs(workpath, exist_ok=True)

    # set downloads folder & path to config file
    downloads = os.path.join(workpath,"Downloads")
    config = os.path.join(workpath, "skyflash.conf")

    if not os.path.isdir(downloads):
        # creating a downloads folder inside it
        os.makedirs(downloads, exist_ok=True)

    # logging to console
    print("App workfolder is {}".format(workpath))
    print("Downloads folder is {}".format(downloads))
    print("Config file is {}".format(config))

    # return it
    return (workpath, downloads, config)

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
        capas = physical_disk.Capabilities
        if capas != None and 7 in capas:
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

def linuxMediaDevices():
    ''' List the media devices that are removable in liunux

    If the major number is 8, that indicates it to be a disk device.

    The minor number is the partitions on the same device:
    - 0 means the entire disk
    - 1 is the primary
    - 2 is extended
    - 5 is logical partitions
    The maximum number of partitions is 15.

    Use `$ sudo fdisk -l` and `$ sudo sfdisk -l /dev/sda` for more information.
    '''

    with open("/proc/partitions", "r") as f:
        devices = []

        for line in f.readlines()[2:]:
            words = [ word.strip() for word in line.split() ]
            major_number = int(words[0])
            minor_number = int(words[1])
            device_name = words[3]

            # disk devices by device name, not partitions
            if (major_number == 8) and not (minor_number % 16):
                devices.append("/dev/" + device_name)

        # data return
        return devices

    # default return if devices are not found
    return False

def getMacDriveInfo():
    '''Get drives info in MacOS

    Must return this: [(dev, label, size)]

    [
        ('/dev/disk2', '', 2369536),
        ('/dev/disk3', 'uD', 3995639808),
        ('/dev/disk4', 'MULTIBOOT', 8300555)
    ]
    '''

    # load the plistlib
    import plistlib

    # get the info
    cmd = ("diskutil list -plist external")
    rx = subprocess.check_output(cmd, shell=True)
    d = plistlib.loads(rx)

    # usdcard and flash drive example
    #
    # {'AllDisks': ['disk1', 'disk1s1', 'disk2', 'disk2s1'],
    # 'AllDisksAndPartitions': [{'Content': 'FDisk_partition_scheme',
    #                             'DeviceIdentifier': 'disk1',
    #                             'Partitions': [{'Content': 'DOS_FAT_32',
    #                                             'DeviceIdentifier': 'disk1s1',
    #                                             'MountPoint': '/Volumes/USD CARD',
    #                                             'Size': 7948205056,
    #                                             'VolumeName': 'USD CARD',
    #                                             'VolumeUUID': '9FEFF8C2-E394-391B-9921-F0E5DD38D522'}],
    #                             'Size': 7948206080},
    #                         {'Content': 'FDisk_partition_scheme',
    #                             'DeviceIdentifier': 'disk2',
    #                             'Partitions': [{'Content': 'Windows_FAT_32',
    #                                             'DeviceIdentifier': 'disk2s1',
    #                                             'MountPoint': '/Volumes/PAVEL',
    #                                             'Size': 7745830912,
    #                                             'VolumeName': 'PAVEL',
    #                                             'VolumeUUID': 'DC01B9FE-840D-346C-99AF-E4C961D2E441'}],
    #                             'Size': 7746879488}],
    # 'VolumesFromDisks': ['USD CARD', 'PAVEL'],
    # 'WholeDisks': ['disk1', 'disk2']}

    data = False

    if len(d["AllDisks"]) > 0:
        # we have suspects
        data = []

        for devs in d["AllDisksAndPartitions"]:
            # direct attributes
            device = "/dev/{}".format(devs["DeviceIdentifier"])
            size = int(devs["Size"])

            # indirect attributes: volume list (mounted partitions)
            parts = ""
            for p in devs["Partitions"]:
                try:
                    parts += " '" + p["VolumeName"] + "'"
                except KeyError:
                    pass

            # clkean extra spaces around
            vols = parts.strip()

            data.append((device, vols, size))

    # return
    return data

def getWinDrivesInfo():
    '''Return a list of available drives in windows
    if possible with a drive label and size in bytes:

    [
        ('E:/', '', 2369536),
        ('F:/', 'CO7WT4G', 3995639808)
    ]
    '''

    # get the data
    data = windowsDevices()
    phydrives = []
    for phy in data:
        size = phy[2]
        letter = []
        label = []
        for d in phy[3]:
            letter.append(d[0])

            # catching an NoneType as the label
            if d[1] != None:
                label.append(d[1])
            else:
                label.append('No-Label')

        phydrives.append((', '.join(letter), ', '.join(label), size))

    # return result
    return phydrives

def getLinDrivesInfo():
    '''Return a list of available drives in linux
    if possible with a drive label and sizes on bytes:

    [
        ('/dev/mmcblk0', '', 8388608),
        ('/dev/mmcblk1', 'BIG uSD Card', 16777216),
        ('/dev/sda', 'MULTIBOOT', 8300555)
    ]
    '''

    # get all removable media devices in the system
    drives = linuxMediaDevices()

    # if we detected a drive, gather the details via lsblk
    if drives:
        d = " ".join(drives)
        js = getDataFromCLI("lsblk -JpbI 8 {}".format(d))
    else:
        # TODO: warn the user
        print("No drives found, detection procedure returned no drive")
        return False

    # is no usefull data exit
    if js is False:
        print("lsblk did not offered info about the drive requested, weird!")
        return False

    # usefull data beyond this point
    finalDrives = []
    data = json.loads(js)

    # getting data, output format is: [(drive, "LABEL", total),]
    for device in data['blockdevices']:
        if device['rm'] == '1':
            name = device['name']
            cap = int(device['size'])
            mounted = ""
            for c in device['children']:
                nn = 'No Label'
                if c['mountpoint'] is not None:
                    nn = c['mountpoint'].split("/")[-1]

                mounted += "{}, ".format(nn)

            finalDrives.append((name, mounted.strip(" ,"), cap))

    # final test
    if len(finalDrives) > 0:
        return finalDrives
    else:
        return False

# fileio overide class to get progress on tarfile extraction
class ProgressFileObject(io.FileIO):
    '''Overide the fileio object to have a callback on progress'''

    def __init__(self, path, *args, **kwargs):
        self._total_size = os.path.getsize(path)

        # callback will be a function passed on progressfn
        if kwargs["progressfn"]:
            self.progfn = kwargs["progressfn"]
            # must remove the progressfn if present from the kwargs to make fileio happy
            kwargs.pop("progressfn")

        io.FileIO.__init__(self, path, *args, **kwargs)

    def read(self, size):
        '''Each time a chunk in read call the progress function if there'''
        if self.progfn:
            # must calc and call the progress callback function
            progress = self.tell() / self._total_size
            self.progfn(progress)

        return io.FileIO.read(self, size)

# signals class, to be used on threads; for all major tasks
class WorkerSignals(QObject):
    '''This class defines the signals to be emmited by the different threaded
    proseses that will be run on this soft'''

    data = pyqtSignal(str)
    error = pyqtSignal(tuple)
    progress = pyqtSignal(float, str)
    result = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, parent=None):
        super(WorkerSignals, self).__init__(parent=parent)

# Generic worker to use in threads
class Worker(QRunnable):
    '''This is the way we manage threads, not by QThread, but a QRunner
     inside a thread pool, in this way we use a generic runable procedure
     of the main object and not a object itself, easy to manage & stable
     '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callbacks to our kwargs
        kwargs['data_callback'] = self.signals.data
        kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''This is the main procedure that runs in the thread pool'''

        try:
            # the thing to do
            result = self.fn(*self.args, **self.kwargs)
        except:
            # report the error back
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            # Return the result of the processing
            self.signals.result.emit(result)
        finally:
            # Done
            self.signals.finished.emit("Done")


    # Instance info
    class SW(enum.IntEnum):
        '''Hold the app status in Windows OS'''
        HIDE = 0
        MAXIMIZE = 3
        MINIMIZE = 6
        RESTORE = 9
        SHOW = 5
        SHOWDEFAULT = 10
        SHOWMAXIMIZED = 3
        SHOWMINIMIZED = 2
        SHOWMINNOACTIVE = 7
        SHOWNA = 8
        SHOWNOACTIVATE = 4
        SHOWNORMAL = 1

    # this is needed for privilege scaling in windows
    class ERROR(enum.IntEnum):
        '''Holds errors and info associated to Windows OS errors'''
        ZERO = 0
        FILE_NOT_FOUND = 2
        PATH_NOT_FOUND = 3
        BAD_FORMAT = 11
        ACCESS_DENIED = 5
        ASSOC_INCOMPLETE = 27
        DDE_BUSY = 30
        DDE_FAIL = 29
        DDE_TIMEOUT = 28
        DLL_NOT_FOUND = 32
        NO_ASSOC = 31
        OOM = 8
        SHARE = 26


    # Instance info
    class SW(enum.IntEnum):
        '''Hold the app status in Windows OS'''
        HIDE = 0
        MAXIMIZE = 3
        MINIMIZE = 6
        RESTORE = 9
        SHOW = 5
        SHOWDEFAULT = 10
        SHOWMAXIMIZED = 3
        SHOWMINIMIZED = 2
        SHOWMINNOACTIVE = 7
        SHOWNA = 8
        SHOWNOACTIVATE = 4
        SHOWNORMAL = 1

    # this is needed for privilege scaling in windows
    class ERROR(enum.IntEnum):
        '''Holds errors and info associated to Windows OS errors'''
        ZERO = 0
        FILE_NOT_FOUND = 2
        PATH_NOT_FOUND = 3
        BAD_FORMAT = 11
        ACCESS_DENIED = 5
        ASSOC_INCOMPLETE = 27
        DDE_BUSY = 30
        DDE_FAIL = 29
        DDE_TIMEOUT = 28
        DLL_NOT_FOUND = 32
        NO_ASSOC = 31
        OOM = 8
        SHARE = 26

def checkUpdates(data_callback, progress_callback):
    '''This routine compare the actual noted version against the one
    in the official repository to check for updates
    
    If we can't ge the file we return null
    If reached and the same False
    If reached and different True
    
    '''

    # DEBUG
    print("Started thread to check for skyflash updates")

    version = ""

    try:
        # try to obtain the file with the latest version
        r = requests.get(updateURL)
        if r.status_code != requests.codes.ok:
            # DEBUG
            print("Getting the version file we received a not good status code of: {}, so cant's check for updates".format(r.status_code))
            return "None"
    except:
        # DEBUG
        print("Getting the version file we raised a exception so cant's check for updates")
        return "None"

    # we get a response
    data = r.text.splitlines()

    for line in data:
        if line == "":
            continue

        if line.startswith("#"):
            continue

        if line.startswith("v"):
            version = line
    
    if version == actualVersion:
        # you are in the same version
        # DEBUG
        print("Same versions, return False: {} = {}".format(version, actualVersion))
        return "False"
    else:
        # yep, you have to updates
        # DEBUG
        print("Different versions, return True: {} = {}".format(version, actualVersion))
        return "True"

def getLatestSkybian(data_callback, progress_callback):
    '''Update the URL from which we need to download the Skybian-vX.Y.z.tar.xz file

    Returns a string containing the url for the download ot the error comments
    '''

    # DEBUG
    print("Started thread to check for skybian URL")

    result = []

    try:
        # try to obtain the file with the latest version
        r = requests.get(skybianVersionFile)
        if r.status_code != requests.codes.ok:
            # DEBUG
            print("Getting the skybian file we received a not good status code of: {}, so cant's check for updates".format(r.status_code))
            return "Error: the server returned a {} code".format(r.status_code)
    except Exception as err:
        return "Error: {}".format(str(err))

    # we get a response
    data = r.text.splitlines()

    for line in data:
        if line == "":
            continue

        if str(line).startswith("#"):
            continue

        if "|" in line:
            result.append(line.split("|"))

    # data can be parsed
    if len(result) == 0:
        # DEBUG
        print("parsed result has zero length")
        return "Error: we can't extract the URL from the Skybian version file"

    # we are concerned now only for the testnet version
    for kind, URL in result:
        if kind == "testnet":
            # DEBUG
            print("Found the URL in the data: {}".format(URL))
            return URL.strip()

    # fail safe
    # DEBUG
    print("No URL found in the data?")
    return "Error: no link provided for the release we are looking for"

def eraseOldVersions(dlfolder, version):
    '''Erase old version files from the download directory

    This is triggered when a new version of skybian is detected & when the
    download of a skybian ends ok
    '''

    # DEBUG
    print("Erasing old files from previous versions in {} folder, actual version is {}".format(dlfolder, version))

    # iterate over the file list
    flist = os.listdir(dlfolder)
    for f in flist:
        # DEBUG
        print("Parsing item: {}".format(f))

        # erase the file of not match the version
        if not version in f:
            item = os.path.join(dlfolder, f)
            # DEBUG
            print("Item does not match version, erasing if file")
            if os.path.isfile(item):
                os.unlink(item)

def calc_speed_eta(size, pr, start_time, time_now):
    '''Calculate the write speed and remaining time from a few values
    
    Output format must be strings ready to print, like this:
    6.2 MBytes/s, 8 minutes 22 seconds
    '''

    try:
        # initial calcs
        time_delta = time_now - start_time
        wrote = size * pr / 100
        remains = size - wrote

        # speed from the time spent in writing the actual amount
        lspeed = wrote / time_delta

        # estimated time for completion
        leta = int(remains / lspeed)
    
    except ZeroDivisionError: 
        return ("please", "wait...")

    return (speed(lspeed), eta(leta)) 
