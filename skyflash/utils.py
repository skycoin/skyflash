# part of skyflash
# misc tools used by skyflash

import sys
import os
import io
import enum
import traceback
import subprocess
import re
import csv
from pprint import pprint

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot

# regular expresions used below, precompiled here.
red = re.compile('Disk \#\d\, Partition \#\d')
rel = re.compile(' [A-Z]: ')

if 'nt' in os.name:
    import ctypes
    # some aliases
    getLogicalDrives = ctypes.windll.kernel32.GetLogicalDrives
    getVolumeInformation = ctypes.windll.kernel32.GetVolumeInformationW
    createUnicodeBuffer = ctypes.create_unicode_buffer
    CreateFile = ctypes.windll.kernel32.CreateFileW
    DeviceIoControl = ctypes.windll.kernel32.DeviceIoControl
    GetLastError = ctypes.windll.kernel32.GetLastError


def shortenPath(fullpath, ccount):
    '''Shorten a passed FS path to a char count size'''

    fpath = fullpath.split(os.sep)
    fpath.reverse()
    spath = fpath[0]

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

def validIP(ip):
    '''Takes a string of a IP and return a tuple:
    true/false and a reason if false
    '''

    # four digits
    digits = str(ip).split('.')
    if len(digits) != 4:
        return (False, "Not enough digits on the IP")

    # from 0 to 255
    for d in digits:
        d = int(d)
        if d > 255 or d < 0:
            return (False, "One of the digits on the IP is not valid")

    # all good
    return (True, "")

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

    if sys.platform in ["win32", "cygwin"]:
        # windows
        path = os.path.expanduser('~')
        # path has the c:\Users\[username] so we need to add the Documents folder
        # Windows has a trick for other langs beside English
        path = os.path.join(path, "Documents")
    elif sys.platform == "darwin":
        # mac
        # TODO reliable way to ident the users Documents folder
        pass
    else:
        # linux
        path = os.path.expanduser('~')

    # now adding the app dir
    path = os.path.join(path, dir)

    # test if the folder is already there
    if not os.path.isdir(path):
        # creating the folder, or not if created
        os.makedirs(path, exist_ok=True)

    # set downloads folder & path to checked file
    downloads = os.path.join(path,"Downloads")
    checked = os.path.join(downloads, ".checked")

    if not os.path.isdir(downloads):
        # creating a downloads folder inside it
        os.makedirs(downloads, exist_ok=True)

    # logging to console
    print("App folder is {}".format(path))
    print("Downloads folder is {}".format(downloads))
    print("Checked file will be {}".format(checked))

    # return it
    return (path, downloads, checked)

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

def getLogicalDrive(phydrive):
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
                record.append(logVol)
                # get the drive letter associated with the logDrive
                l = getLetter(logVol)
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

def getPHYDrives():
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

    data = []

    for r in listd:
        if len(r) == 0:
            continue

        d = dict()

        # check if the media is removable (cap has #7)
        capas = r[capa].strip('{}').split(';')
        if '7' in capas:
            d["phydrive"] = r[phydrive]
            d['drives'] = getLogicalDrive(r[phydrive])
            d["interface"] = r[interface]
            d["desc"] = r[descDirty]
            d["size"] = r[size]
            data.append(d)

    # sample output
    # [{'desc': 'USBSTOR\\DISK&amp;VEN_VERBATIM&amp;PROD_STORE_N_GO&amp;REV_PMAP\\900067B77116E868&amp;0',
    # 'drives': [['Disk #1, Partition #0',
    #             'F:',
    #             'MULTIBOOT',
    #             '\\\\?\\Volume{62c491be-0ec2-11e9-a1ea-080027b4fa52}\\']],
    # 'interface': 'USB',
    # 'phydrive': '\\\\.\\PHYSICALDRIVE1',
    # 'size': '7739988480'},
    # {'desc': 'USBSTOR\\DISK&amp;VEN_MASS&amp;PROD_STORAGE_DEVICE&amp;REV_1.00\\121220160204&amp;0',
    # 'drives': [['Disk #2, Partition #0',
    #             'H:',
    #             '[No Label]',
    #             '\\\\?\\Volume{37189f6b-5e76-11e9-a1fd-0800275fd42d}\\']],
    # 'interface': 'USB',
    # 'phydrive': '\\\\.\\PHYSICALDRIVE2',
    # 'size': '8052549120'}]

    return data

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
    hDevice = CreateFile(physicalDevice, 1|2, 1|2, 0, 3, 0, None)
    if hDevice == -1:
        print("Cannot open the device {}. Error code: {}.".format(physicalDevice, GetLastError()))
        return
    else:
        print("Device {} opened.".format(physicalDevice))

    # Open the volume
    hVolume = CreateFile(volumeGUID, 1|2, 1|2, 0, 3, 0, None)
    if hDevice == -1:
        print("Cannot open the volume {}. Error code: {}.".format(volumeGUID,
        ID, GetLastError()))
        return
    else:
        print("Volume {} dismounted.".format(volumeGUID))


    # Lock the device
    if not DeviceIoControl(hDevice, 589848, None, 0, None, 0, None, None):
        print("Cannot lock the volume {}. Error code: {}.".format(volumeGUID, GetLastError()))
        return
    else:
        print("Device {} locked.".format(physicalDevice))

    # Dismount the device
    if not DeviceIoControl(hDevice, 589856, None, 0, None, 0, None, None):
        print("Cannot dismount the volume {}. Error code: {}.".format(volumeGUID, GetLastError()))
        return
    else:
        print("Device {} dismounted.".format(physicalDevice))

    # Close opened handlers:
    # CloseHandle(hVolume)
    # CloseHandle(hDevice)
    return

# fileio overide class to get progress on tarfile extraction
# TODO How to overide a class from a module
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
