#!/usr/bin/env python3

# main imports
import os
import io
import sys
import subprocess
import webbrowser
import time
import traceback
import tarfile
import ssl
import hashlib
from urllib.request import Request, urlopen

# GUI imports
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import *

# environment vars
# TODO, set final real URLS
skybianUrl = "http://localhost:8080/skybian.tar.gz"
# skybianUrl = "https://github.com/skycoin/skycoin/archive/develop.zip"
manualUrl = "http://github.com/simelo/skyflash"

# utils class
class Utils(object):
    '''This is a basic class to hold procedures & functions that does not belongs
    to any other part or class in the project, such as validation, conversion, 
    formatting, etc. As the name implies a utils tool box'''

    def __init__(self):
        return super(Utils, self).__init__()

    def shortenPath(self, fullpath, ccount):
        '''Shorten a passed FS path to a char count size'''

        fpath = fullpath.split(os.sep)
        fpath.reverse()
        spath = fpath[0]
        count = len(spath)

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

    def eta(self, secs):
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

    def speed(self, speed):
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

    def size(self, size):
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
            out = "{} bytes".format(int(speed))

        return out


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
        return super(WorkerSignals, self).__init__(parent=parent)


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


# main object definition
class skyFlash(QObject):
    '''Main/Base object for all procedures and properties, this is the core
    of our App
    '''

    ### init procedure
    def __init__(self, parent=None):
        self.downloadActive = False
        self.downloadOk = False
        self.downloadedFile = ""
        self.skybianFile = ""
        self.extractionOK = False
        self.digestAlgorithm = ""
        self.digest = ""
        self.skybianFile = ""

        # set the working dir for the downloads and extraction to a folder
        # named skyflash on the users home, create it if not there
        self.localPath = self.setPath("Skyflash")

        return super(skyFlash, self).__init__(parent=parent)

    # some variables
    localPath = ""
    digestAlgorithm = ""
    digest = ""

    #### registering Signals to emit to QML GUI

    # status bar
    setStatus = pyqtSignal(str, arguments=["msg"])

    # download signals
    # target is download label
    dData = pyqtSignal(str, arguments=["data"])
    # target is proogress bar
    dProg = pyqtSignal(float, arguments=["percent"])
    # target is hide download buttons
    dDone = pyqtSignal()
    # target is show download buttons
    dStart = pyqtSignal()

    # download flags
    downloadActive = False
    downloadOk = False

    # files handling vars
    downloadedFile = ""
    skybianFile = ""

    # extraction flags
    extractionOk = False

    # network signals
    netConfig = pyqtSignal()

    # thread pool
    threadpool = QThreadPool()

    # set the timeout for threads on done
    threadpool.setExpiryTimeout(3000)

    # download callbacks to emit signals to QML nd others

    #  download ones

    def downloadFileData(self, data):
        '''Update the label beside the buttons in the download box on the UI'''

        self.dData.emit(data)

    def downloadFileProg(self, percent, data):
        '''Update the progress bar and status bar about the task progress'''

        self.dProg.emit(percent)
        self.setStatus.emit(data)

    def downloadFileError(self, error):
        '''Stop the threaded task and produce feedback to the user'''

        # stop the download & reset env
        self.cleanWorkspace()

        # download error feedback
        self.dData.emit("Download error...")
        self.setStatus.emit("An error ocurred, please check the network.")
        etype, eval, etrace = error
        print("An error ocurred:\n{}".format(eval))

    def downloadFileResult(self, file):
        '''Receives the result of the download: the path to the downloaded file '''

        # debug
        print("Download result: {}".format(file))

        if self.downloadOk:
            self.downloadedFile = file
            # TODO adjust the size of the path
            self.dData.emit("Skybian compressed file is: " + utils.shortenPath(file, 32))
        else:
            # reset the env
            self.cleanWorkspace()

            # specific feedback 
            self.dData.emit("Download canceled or error")
            self.setStatus.emit("Download canceled or error happened")

    def downloadFileDone(self, result):
        '''End of the download task'''

        # debug
        print("Download Done!")

        # check status of download
        if self.downloadOk and self.downloadedFile != "":
            self.dDone.emit()
            
            # call to handle the download (a img or a compressed one)
            self.downloadProcess()

    # extract ones

    def extractFileResult(self, result):
        '''Callback that receives the signal for a extraction finished, an
        argument is passes, result, it's true or false to flag success or failure'''

        # debug
        print("Extraction result: {}".format(result))

        if result:
            self.extractionOk = True
            self.dData.emit("Extraction finished")

    def extractFileDone(self):
        '''Callback that is flagged once the extraction was ended.'''

        # debug
        print("Extraction Done!")

        # must check for checksums to validate downloads
        self.sumsCheck()

        # TODO, this is not working
        # if self.extractionOK:
        #     # success must call for a sha1sum check
        #     print("Success extraction")

    def extractFileError(self, error):
        '''Process the error of the extraction'''

        # stop the extraction & reset env
        self.cleanWorkspace()

        # specific feedback
        self.dData.emit("Extraction error...")
        self.setStatus.emit("An error ocurred, corrupt file?")
        etype, eval, etrace = error
        print("An error ocurred:\n{}".format(eval))

    @pyqtSlot()
    def downloadSkybian(self):
        '''Slot that receives the stat download signal from the UI'''

        # check if there is a thread already working there
        downCount = self.threadpool.activeThreadCount()
        if downCount < 1:
            # rise flag
            self.downloadActive = True

            # set label to starting
            self.dData.emit("Download starting...")

            # init download process
            self.down = Worker(self.skyDown)
            self.down.signals.data.connect(self.downloadFileData)
            self.down.signals.progress.connect(self.downloadFileProg)
            self.down.signals.result.connect(self.downloadFileResult)
            self.down.signals.error.connect(self.downloadFileError)
            self.down.signals.finished.connect(self.downloadFileDone)

            # init worker
            self.threadpool.start(self.down)
        else:
            # if you clicked it during a download, then you want to cancel
            # just rise the flag an the thread will catch it and stop
            self.downloadActive = False
            self.downloadOk = False

            # set label to stopping
            self.dData.emit("Download canceled...")

    # download skybian, will be instantiated in a thread
    def skyDown(self, data_callback, progress_callback):
        '''Download task, this will runs in a threadpool

        Result returned must be string and in this case will be the
        path for the downloaded file or an empty string on error/cancel

        This method is wrapped by the thread and will catch any errors
        upstream so no need to handle it here
        '''

        # take url for skybian from upper
        url = skybianUrl

        # DEBUG
        print("Downloading from: {}".format(url))

        headers = {}
        headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
        r = Request(url, headers=headers)

        if url.startswith("https"):
            # prepare the https context
            scontext = ssl.SSLContext(ssl.PROTOCOL_TLS)
            req = urlopen(r, context=scontext)
        else:
            req = urlopen(r)

        # check if we have a size or it's not known (wtf Github!)
        info = req.info()
        if not "Content-Length" in info:
            self.size = -1
        else:
            self.size = int(req.info()['Content-Length'])

        # extract filename
        fileName = url.split("/")[-1]

        # emit data of the download
        if self.size > 0:
            data_callback.emit("Downloading {:04.1f} MB".format(self.size/1000/1000))
        else:
            data_callback.emit("Downloading size is unknown")

        # start download
        downloadedChunk = 0

        # chuck size @ 100KB
        blockSize = 102400
        filePath = os.path.join(self.localPath, fileName)
        startTime = 0
        elapsedTime = 0

        # DEBUG
        print("Downloading to: {}".format(filePath))

        with open(filePath, "wb") as downFile:
            startTime = time.time()
            while True:
                chunk = req.read(blockSize)
                if not chunk:
                    print("\nDownload Complete.")
                    break

                downloadedChunk += len(chunk)
                downFile.write(chunk)
                if self.size > 0:
                    progress = (float(downloadedChunk) / self.size) * 100
                else:
                    progress = -1

                # calc speed and ETA
                elapsedTime = time.time() - startTime
                bps = int(downloadedChunk/elapsedTime) # b/s
                if self.size > 0:
                    etas = int((self.size - downloadedChunk)/bps) # seconds

                # emit progress
                if self.size > 0:
                    prog = "{:.1%}, {}, {} to go".format(progress/100,  utils.speed(bps), utils.eta(etas))
                else:
                    prog = "{} so far at {}, unknown ETA".format(utils.size(downloadedChunk),  utils.speed(bps))

                # emit progress
                progress_callback.emit(progress, prog)

                # check if the terminate flag is raised
                if not self.downloadActive:
                    downFile.close()
                    os.unlink(downFile)
                    return ""

        # close the file handle
        if downFile:
            downFile.close()

        self.downloadOk = True

        # return the local filename
        return filePath

    # load skybian from a local file
    @pyqtSlot(str)
    def localFile(self, file):
        '''Slot that receives the local folder picked up to process'''

        if file is "":
            self.setStatus.emit("You selected nothing, please try again")
            return
        
        # TODO, check on windows
        if file.startswith("file:///"):
            file = file.replace("file://", "")

        print("Selected file is " + file)

        # try to read a chunk of it
        try:
            self.bimg = open(file, 'rb')
            dump = self.bimg.read(10)
            self.bimg.close()
        
        except:
            # TODO exact error
            self.setStatus.emit("Selected file is not readable.")
            return

        # all seems good, emit and go on
        self.downloadOk = True
        self.downloadFileResult(file)
        time.sleep(3)
        self.downloadFileDone("OK")

    def downloadProcess(self):
        '''Process a downloaded/locally picked up file, it can be a .img or a
        .tar.[gz|xz] one.
        
        If a compressed must decompress and check sums to validate and/or
        if a image must check for a fingerprint to validate
        
        If error produce feedback, if ok, continue.
        '''
        
        # determine the type of file and the curse of actions
        segPath = self.downloadedFile.split(".")
        if segPath[-1] in ["tar", "gz", "xz"]:
            # compressed file, handle it on a thread
            self.extract = Worker(self.extractFile)
            self.extract.signals.data.connect(self.downloadFileData)
            self.extract.signals.progress.connect(self.downloadFileProg)
            self.extract.signals.result.connect(self.extractFileResult)
            self.extract.signals.error.connect(self.extractFileError)
            self.extract.signals.finished.connect(self.extractFileDone)

            # init worker
            self.threadpool.start(self.extract)

        elif segPath[-1] in "img":
            # plain image
            self.skybianFile = self.downloadedFile
            return

        else:
            # other unknown case
            # TODO Warn the user, what to do next?
            pass

    def extractFile(self, data_callback, progress_callback):
        '''Extract a file compressed with tar and xz|gz of the skybian base file.

        Result returned must be string that will be converted to boolean so we stick
        to strings 1|0

        This method is wrapped by the thread and will catch any errors upstream
        so no need to handle it here
        '''

        # change cwd temporarily to extract the files
        cwd = os.getcwd()
        os.chdir(self.localPath)

        # tar extraction progress
        def tarExtractionProgress(percent):
            '''Callback used to update the progress on file extraction, it reuse the
            self.downloadFileProg(percent, data) function'''

            data = "Extracting downloaded file {:.1%}".format(percent)
            progress_callback.emit(percent * 100, data)

        # update status
        data_callback.emit("Extracting the file, please wait...")
        tar = tarfile.open(fileobj=ProgressFileObject(self.downloadedFile, progressfn=tarExtractionProgress))
        tar.extractall()
        tar.close()
        self.extractionOk = True

        # all ok return to cwd and close the thread
        os.chdir(cwd)

        # return
        return "1"

    # open the manual in the browser
    @pyqtSlot()
    def openManual(self):
        '''Opens the manual in a users's default browser'''

        if sys.platform in ["win32", "cygwin"]:
            try:
                os.startfile(manualUrl)
            except:
                webbrowser.open(manualUrl)

        elif sys.platform == "darwin":
            subprocess.Popen(["open", manualUrl])

        else:
            try:
                subprocess.Popen(["xdg-open", manualUrl])
            except OSError:
                print("Please open a browser on: " + manualUrl)

    def cleanWorkspace(self):
        '''Cleans the workspace, erase any temp/work file and resets the
        interface to start all over again like a fresh start, erasing
        vars from the previous run'''

        # erase any working file
        filePatterns = ["img", "gz", "xz", "sha1", "md5"]
        for item in os.listdir(self.localPath):
            itemExtension = item.split(".")[-1]
            if itemExtension in filePatterns:
                print("Erasing file {}".format(item))
                os.unlink(self.localPath + "/" + item)

        # vars reset
        self.downloadedFile = ""
        self.downloadOk = False
        self.downloadActive = False
        self.skybianFile = ""
        self.extractionOk = False

        # GUI reset
        self.sStart.emit()

    def setPath(self, dir):
        '''Pick the correct path for the current OS and create it if not there
        This is the path in with we will download, extract, create, etc.
        '''

        if sys.platform in ["win32", "cygwin"]:
            # windows
            # TODO reliable way to ident the users Documents folder
            pass

        elif sys.platform == "darwin":
            # mac
            # TODO reliable way to ident the users Documents folder
            pass

        else:
            # linux
            path = os.path.join(os.path.expanduser('~'), dir)

        # test if the folder is already there
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)

        # return it
        return path

    def sumsCheck(self):
        '''Detects and load the digest sums to check integrity of the
        image file, it will try to detect this ones:

        sha256, sha1 & md5

        The first found will be used to check the
        image in a thread
        '''

        # list of supported ext/sums digest
        digestAlgorithms = ["sha256", "sha1", "md5"]
        digestFile = ""
        digestType = ""

        # detect the sums files
        # files = [x for x in os.listdir(self.localPath) if os.path.isfile(x)]
        files = os.listdir(self.localPath)
        for file in files:
            print("Found file: {}".format(file))
            ext = file.split(".")[-1]
            if ext in digestAlgorithms:
                digestFile = os.path.join(self.localPath, file)
                digestType = ext
                print(">>> file is a checksum one")
                break

        # can't find a valid digest file
        if not digestType:
            # TODO WARNING no DIGEST to check against
            return "error"

        # prepare to check the digest against the image in a thread
        try:
            sf = open(digestFile, 'r')
        except OSError:
            print("An error opening the file happened...")
            raise

        # loading values
        try:
            digest, imgFile = sf.readline().split(" ")
        except:
            print("Error, checksum file {} is empty?".format(imgFile))

        # cleaning the filename (it has a starting * and ends with a newline)
        imgFile = os.path.join(self.localPath, imgFile.strip("*"))
        imgFile = imgFile.strip("\n")

        # DEBUG
        print("File: {}\nDigest: {}\nDigest Algorithm is: {}".format(imgFile, digest, digestType))

        self.digestAlgorithm = digestType
        self.digest = digest
        self.skybianFile = imgFile

        # start the checksum thread
        self.cksum = Worker(self.cksumCheck)
        self.cksum.signals.data.connect(self.downloadFileData)
        self.cksum.signals.progress.connect(self.downloadFileProg)
        # self.cksum.signals.result.connect(self.extractFileResult)
        # self.cksum.signals.error.connect(self.extractFileError)
        # self.cksum.signals.finished.connect(self.extractFileDone)

        # init worker
        self.threadpool.start(self.cksum)

        return

    def cksumCheck(self, data_callback, progress_callback):
        '''Check the checksum detected for the skybian base file

        Result returned must be string that will be converted to boolean so we stick
        to strings 1|0

        This method is wrapped by the thread and will catch any errors upstream
        so no need to handle it here
        '''

        # object checksum creation the fast way, there is a argument passing way (simpler)
        # but docs discourage it as slow
        if self.digestAlgorithm == "md5":
            cksum = hashlib.md5()
        elif self.digestAlgorithm == "sha1":
            cksum = hashlib.sha1()
        else:
            print("Digest algorithm {} is not supported yet".format(self.digestAlgorithm))
            return

        # get the file and it's size, etc
        fileSize = os.path.getsize(self.skybianFile)
        file = open(self.skybianFile, "rb")
        actualPosition = 0
        portionSize = 8192

        # user feedback
        data_callback.emit("Integrity checking, please wait...")

        # main loop
        file.seek(0)
        while actualPosition < fileSize:
            data = file.read(portionSize)
            cksum.update(data)

            # progress and cycle update
            actualPosition += portionSize
            percent = actualPosition / fileSize

            data = "Integrity checking {:.1%}".format(percent)
            progress_callback.emit(percent * 100, data)

        # check the calculated digest
        calculatedDigest = cksum.hexdigest()
        print("Official Sum: {}".format(self.digest))
        print("Calculated:   {}".format(calculatedDigest))


if __name__ == "__main__":
    '''Run the script'''

    try:
        # instance of utils
        utils = Utils()

        # GUI app
        app = QGuiApplication(sys.argv)

        # main workspace, skyflash object
        skyflash = skyFlash()

        # startting the UI engine
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("skf", skyflash)
        engine.load("skyflash.qml")
        engine.quit.connect(app.quit)

        # main GUI call
        sys.exit(app.exec_())
    except SystemExit:
        sys.exit("By, see you soon.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
        sys.exit(-1)


