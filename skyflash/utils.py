# part of skyflash
# misc tools used by skyflash

import sys
import os
import io
import enum
import traceback
import subprocess
import ctypes

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot

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
    '''Return False if the soft is not in the system or the path string if true'''

    try:
        output = subprocess.check_output("which {}".format(soft), shell=True)
    except subprocess.CalledProcessError:
        return False

    if output == '':
        output = False

    return bytes(output).decode().strip("\n")

# use this function to request higher privileges on Windows
if sys.platform in ["win32", "cygwin"]:

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


    def bootstrap():
        '''
        This functions check if the script is runing on high privileges, if not
        the as them to the user using the default Windows OS UAC mechanism
        handling any error in the process
        '''

        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("You are not admnin")
        else:
            print("You are Admin")

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
