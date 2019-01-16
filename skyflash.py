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
import logging
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

# image config file position and size
imageConfigAddress = 3670016
imageConfigDataSize = 256

# utils class
class Utils(object):
    '''This is a basic class to hold procedures & functions that does not belongs
    to any other part or class in the project, such as validation, conversion,
    formatting, etc. As the name implies a utils tool box'''

    def __init__(self):
        super(Utils, self).__init__()

    def shortenPath(self, fullpath, ccount):
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
            out = "{} bytes".format(int(size))

        return out

    def validIP(self, ip):
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


# main object definition
class skyFlash(QObject):
    '''Main/Base object for all procedures and properties, this is the core
    of our App
    '''

    ### init procedure
    def __init__(self, parent=None):
        self.downloadActive = False
        self.downloadOk = False
        self.downloadSize = 0
        self.downloadedFile = ""
        self.skybianFile = ""
        self.extractionOK = False
        self.digestAlgorithm = ""
        self.digest = ""
        self.skybianFile = ""
        self.cksumOk = False

        # set the working dir for the downloads and extraction to a folder
        # named skyflash on the users home, create it if not there
        self.localPath = self.setPath("Skyflash")

        # log
        logfile = os.path.join(self.localPath, "skyflash.log")
        logging.basicConfig(filename=logfile, level=logging.DEBUG)
        self.logStart()

        return super(skyFlash, self).__init__(parent=parent)

    # some variables
    localPath = ""
    digestAlgorithm = ""
    digest = ""
    netGw = ""
    netDns = ""
    netManager = ""
    netNodes = ""

    #### registering Signals to emit to QML GUI

    # status bar
    setStatus = pyqtSignal(str, arguments=["msg"])

    # QT QML signals
    # target is download label
    dData = pyqtSignal(str, arguments=["data"])
    # target is proogress bar
    dProg = pyqtSignal(float, arguments=["percent"])
    # target is hide download buttons
    dDone = pyqtSignal()
    # target is show download buttons
    sStart = pyqtSignal()
    # target is warnDialog Box rise
    uiWarning = pyqtSignal(str, str, arguments=["title", "text"])
    # target is errorwarnDialog Box rise
    uiError = pyqtSignal(str, str, str, arguments=["title", "text", "details"])
    # build single process show single file build progress
    bsProg = pyqtSignal(float, arguments=["percent"])
    # build overal progress, show overall progress for the whole image build
    boProg = pyqtSignal(float, arguments=["percent"])

    # download flags
    downloadActive = False
    downloadOk = False

    # files handling vars
    downloadSize = 0
    downloadedFile = ""
    skybianFile = ""

    # extraction flags
    extractionOk = False

    # checksum vars
    cksumOk = False

    # network signals
    netConfig = pyqtSignal()
    buildImages = pyqtSignal()

    # thread pool
    threadpool = QThreadPool()

    # set the timeout for threads on done
    threadpool.setExpiryTimeout(500)

    # callbacks to emit signals to QML and others

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
        self.setStatus.emit("Please try again")
        etype, eval, etrace = error
        logging.debug("An error ocurred:\n{}".format(eval))
        self.uiError.emit("Network Error?", "Please check your network connection, the download of the Skybian base file failed, it's mostly related to network problems.", str(eval))

    def downloadFileResult(self, file):
        '''Receives the result of the download: the path to the downloaded file '''

        # debug
        logging.debug("Download result: {}".format(file))
        logging.debug("Download ok : {}".format(str(self.downloadOk)))

        # validation
        if file != "" and self.downloadOk:
            # all good
            self.downloadedFile = file
        else:
            # reset the env
            self.cleanWorkspace()

            # specific feedback
            self.setStatus.emit("Download canceled or error happened")
            self.uiError.emit("Download failed!", "Download process failed silently, mostly due to connection issues, please try again", "")

    def downloadFileDone(self, result):
        '''End of the download task'''

        # debug
        logging.debug("Download Done:")

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
        logging.debug("Extraction result: {}".format(result))

        if result:
            self.extractionOk = True
            self.dData.emit("Extraction finished")
        else:
            # extraction finished with no errors, but failed...
            self.uiWarning.emit("Extraction failed", "Extraction finished with no error, but was no success, please report this warning to the developers")

    def extractFileDone(self):
        '''Callback that is flagged once the extraction was ended.'''

        # debug
        logging.debug("Extraction Done:")

        # must check for checksums to validate downloads
        self.sumsCheck()

        # TODO, this is not working
        # if self.extractionOK:
        #     # success must call for a sha1sum check
        #     logging.debug("Success extraction")

    def extractFileError(self, error):
        '''Process the error of the extraction'''

        # stop the extraction & reset env
        self.cleanWorkspace()

        # specific feedback
        self.setStatus.emit("Please try again")
        etype, eval, etrace = error
        logging.debug("An error ocurred:\n{}".format(eval))
        self.uiError.emit("Extraction error", "There was an error extracting the downloaded file, this is mainly due to a corruped download, please try again.", str(eval))

    # cksum ones

    def cksumResult(self, result):
        '''Callback that receives the signal for a cksum finished, an
        argument is passed, result, it's true or false to flag success or failure'''

        # debug
        logging.debug("Checksum verification result: {}".format(result))

        if result:
            self.cksumOk = True
            self.dData.emit("Skybian image verified!")
            logging.debug("Checksum verification result is ok")
        else:
            self.cksumOk = False
            self.dData.emit("Skybian image can't be verified!")
            logging.debug("Checksum verification failed: hash differs!")
            self.uiError.emit("Skybian image can't be verified!", "The Skybian image integrity check ended with a different fingerprint or a soft error, this image is corrupted or a soft error happened, please start again.", "Downloaded & computed Hash differs")

    def cksumDone(self):
        '''Callback that is flagged once the checkum was ended.'''

        # debug
        logging.debug("Checksum verification done")

        if self.cksumOk:
            # success must call for a sha1sum check
            logging.debug("Checksum verification is a success!")
            # next step
            self.netConfig.emit()
            self.buildImages.emit()

    def cksumError(self, error):
        '''Process the error of the checksum, this only process error in the
        process, a completed checksum but not matching is handled by result
        not in this.
        '''

        # stop the extraction & reset env
        self.cleanWorkspace()

        # specific feedback
        self.dData.emit("Checksum process error...")
        self.setStatus.emit("An error ocurred, can't do the image verification")
        etype, eval, etrace = error
        logging.debug("An error ocurred while verifying the checksum:\n{}".format(eval))
        self.uiError.emit("Integrity check failed!", "The Skybian image integrity check failed with an error, please report this to the developers", str(eval))

    # build ones

    def buildData(self, data):
        ''''''
        pass

    def buildProg(self, percent, data):
        '''Update two progressbar and a status bar in the UI

        The data came as a percent of the single image, and the
        data part carries the comment for the status bar and the
        overall progress that we must cut out to pass to the
        corresponding progress bar
        '''

        # split data
        d = data.split("|")
        self.bsProg.emit(percent)
        self.setStatus.emit(d[0])
        self.boProg.emit(float(d[1]))

    def buildResult(self, data):
        ''''''
        pass

    def buildError(self, data):
        ''''''
        pass

    def buildDone(self, data):
        ''''''
        pass

    @pyqtSlot()
    def downloadSkybian(self):
        '''Slot that receives the stat download signal from the UI'''

        # check if there is a thread already working there
        downCount = self.threadpool.activeThreadCount()
        if downCount < 1:
            # rise flag
            self.downloadActive = True

            # set label to starting
            self.dData.emit("Downloading...")

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
        logging.debug("Downloading from: {}".format(url))

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
            self.downloadSize = -1
            logging.debug("Download file size is unknown...")
        else:
            self.downloadSize = int(req.info()['Content-Length'])
            logging.debug("Download file size is {:0.1f}MB".format(self.downloadSize/1000/1000))

        # extract filename
        fileName = url.split("/")[-1]

        # emit data of the download
        if self.downloadSize > 0:
            data_callback.emit("Downloading {:04.1f} MB".format(self.downloadSize/1000/1000))
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
        logging.debug("Downloading to: {}".format(filePath))

        with open(filePath, "wb") as downFile:
            startTime = time.time()
            while True:
                chunk = req.read(blockSize)
                if not chunk:
                    logging.debug("Download Complete.")
                    break

                downloadedChunk += len(chunk)
                downFile.write(chunk)
                if self.downloadSize > 0:
                    progress = (float(downloadedChunk) / self.downloadSize) * 100
                else:
                    progress = -1

                # calc speed and ETA
                elapsedTime = time.time() - startTime
                bps = int(downloadedChunk/elapsedTime) # b/s
                if self.downloadSize > 0:
                    etas = int((self.downloadSize - downloadedChunk)/bps) # seconds

                # emit progress
                if self.downloadSize > 0:
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

        # if download size is known and is not meet rise error
        if self.downloadSize != -1:
            # check if downloaded file is that size
            realSize = os.path.getsize(filePath)

            # debug
            logging.debug("Download size check:\nRemote size: {}\nLocal size: {}".format(self.downloadSize, realSize))

            if int(realSize) != int(self.downloadSize):
                # ops! download truncated
                self.downloadOk = False
                logging.debug("Error! file size differs")
                return ""

        # unknown length or correct length and downloaded fully
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

        # clean the path depending on the OS
        if sys.platform in ["win32", "cygwin"]:
            # file is like this file:///C:/Users/Pavel/Downloads/Skybian-0.1.0.tar.xz
            # need to remove 3 slashes
            file = file.replace("file:///", "")
        else:
            # working on linux, like this: file:///home/pavel/Downloads/Skybian-0.1.0.tar.xz
            # TODO test os MacOS
            file = file.replace("file://", "")

        logging.debug("Selected file is " + file)

        # try to read a chunk of it
        try:
            self.bimg = open(file, 'rb')
            dump = self.bimg.read(10)
            self.bimg.close()
        except:
            # TODO exact error
            self.setStatus.emit("Selected file is not readable.")
            raise
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

            # TODO user selected a image file, disable this option? skip verification?
            return

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

            # static var, to avoid saturation of the QML interface with signals
            # we will emit signals only on > 0.2 changes
            oldpercent = 0

            if percent - oldpercent > 0.2:
                oldpercent = percent
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

        logging.debug("Trying to open the manual page on the browser, wait for it...")

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
                logging.debug("Please open a browser on: " + manualUrl)

    def cleanWorkspace(self):
        '''Cleans the workspace, erase any temp/work file and resets the
        interface to start all over again like a fresh start, erasing
        vars from the previous run'''

        logging.debug("Clean workspace called, cleaning the house")

        # erase any working file
        filePatterns = ["img", "gz", "xz", "sha1", "md5"]
        for item in os.listdir(self.localPath):
            itemExtension = item.split(".")[-1]
            if itemExtension in filePatterns:
                logging.debug("Erasing file {}".format(item))
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
        print("App folder is {}".format(path))

        # test if the folder is already there
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
            print("Creating app folder")

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
        files = os.listdir(self.localPath)
        for file in files:
            ext = file.split(".")[-1]
            if ext in digestAlgorithms:
                logging.debug("Found checksum file: {}".format(file))
                digestFile = os.path.join(self.localPath, file)
                digestType = ext
                break

        # can't find a valid digest file
        if not digestType:
            # TODO WARNING no DIGEST to check against
            return "error"

        # prepare to check the digest against the image in a thread
        try:
            sf = open(digestFile, 'r')
        except OSError:
            logging.debug("An error opening the checksum file happened...")
            raise

        # loading values
        try:
            digest, imgFile = sf.readline().split(" ")
        except:
            logging.debug("Error, checksum file {} is empty?".format(imgFile))
            raise

        # cleaning the filename (it has a starting * and ends with a newline)
        imgFile = os.path.join(self.localPath, imgFile.strip("*"))
        imgFile = imgFile.strip("\n")

        # DEBUG
        logging.debug("checksum details:\nFile: {}\nDigest: {}\nDigest Algorithm is: {}".format(imgFile, digest, digestType))

        self.digestAlgorithm = digestType
        self.digest = digest
        self.skybianFile = imgFile

        # start the checksum thread
        self.cksum = Worker(self.cksumCheck)
        self.cksum.signals.data.connect(self.downloadFileData)
        self.cksum.signals.progress.connect(self.downloadFileProg)
        self.cksum.signals.result.connect(self.cksumResult)
        self.cksum.signals.error.connect(self.cksumError)
        self.cksum.signals.finished.connect(self.cksumDone)

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
            logging.debug("Digest algorithm {} is not supported yet".format(self.digestAlgorithm))
            return

        # get the file and it's size, etc
        fileSize = os.path.getsize(self.skybianFile)
        file = open(self.skybianFile, "rb")
        actualPosition = 0
        portionSize = 81920

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
        logging.debug("Official Sum: {}".format(self.digest))
        logging.debug("Calculated:   {}".format(calculatedDigest))

        if self.digest == calculatedDigest:
            # success, image integrity preserved
            return "1"
        else:
            # failure
            return ""

    def logStart(self):
        '''Initializate the logging, send some start of log info to the file'''

        logging.info("")
        logging.info("====================================================")
        logging.info("Logging started at {}".format(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())))
        logging.info("====================================================")
        logging.info("")

    @pyqtSlot(str, str, str, str)
    def imagesBuild(self, gw, dns, manager, nodes):
        '''Receives the Button order to build the images, passed arguments are:

        gw: the network gateway
        dns: the DNS to use in the format "1.2.3.4, 4.3.2.1" (must pass it along as is)
        manager: ip of the manager
        nodes: number of nodes to build
        '''

        # debug
        logging.debug("Build received data is:\nGW: '{}'\nDNS: '{}'\nManager: '{}'\nNodes '{}'".format(gw, dns, manager, nodes))

        # validation #1, are the manger, dns and gw valid ips?
        gwValid, reason = utils.validIP(gw)
        if not gwValid:
            self.uiError.emit("Validation error", "The GW IP entered is not valid, please check that", reason)
            logging.debug("GW ip not valid: {}".format(gw))
            return

        managerValid, reason = utils.validIP(manager)
        if not managerValid:
            self.uiError.emit("Validation error", "The Manager IP entered is not valid, please check that", reason)
            logging.debug("Manager ip not valid: {}".format(mnager))
            return

        # validation #2, dns, two and valid ips
        dnss = dns.split(' ')
        dnss[0] = dnss[0].strip(',')
        if len(dnss) != 2:
            reason = "DNS must be in the format '1.2.3.4, 2.3.4.5'"
            self.uiError.emit("Validation error", "The DNS string entered is not valid, please check that.", reason)
            logging.debug("DNS string is not valid: '{}'".format(dns))
            return

        dns1Valid, reason = utils.validIP(dnss[0])
        if not dns1Valid:
            self.uiError.emit("Validation error", "The first IP on the DNS is not valid, please check that.", reason)
            logging.debug("DNS1 IP is not valid: '{}'".format(dns))
            return

        dns2Valid, reason = utils.validIP(dnss[1])
        if not dns2Valid:
            self.uiError.emit("Validation error", "The second IP on the DNS is not valid, please check that.", reason)
            logging.debug("DNS2 IP is not valid: '{}'".format(dns))
            return

        # validation #3, gw and manager must be on the same IP range
        if gw[0:gw.rfind('.')] != manager[0:manager.rfind('.')]:
            self.uiError.emit("Validation error", "The manager and the gw are not in the same sub-net, please check that", "")
            logging.debug("Base address for the net differs in gw/manager: '{1} vs. {2}'".format(gw, manager))
            return

        # validation #4, node counts + ip is not bigger than 255
        endip = int(manager[manager.rfind('.') + 1:]) + int(nodes)
        if endip > 255:
            self.uiError.emit("Validation error", "The node IP distribution is beyond 255, please lower your manager ip",
                "The IP of the nodes are distributed from the manager IP and up, if you set the manager node IP so high the node count may not fit")
            logging.debug("Manager IP to high, last node will be {} and that's not possible".format(endip))
            return

        # validation #5, gw not in manager & nodes range
        if int(gw[gw.rfind('.') + 1:]) in range(int(manager[manager.rfind('.') + 1:]), endip):
            self.uiError.emit("Validation error", "Please check your GW, Manager & Node selection, the GW is one of the Nodes or Manager IPs",
                "When we distribute the manager & nodes IP we found that the GW is one of that IP and that's wrong")
            logging.debug("GW ip is on generated nodes range.".format(dns))
            return

        # if you reached this all is good, set the network vars on top of the object
        self.netGw = gw
        self.netDns = dns
        self.netManager = manager
        self.netNodes = nodes

        # Starting to build the nodes.
        # thead start
        self.build = Worker(self.buildTheImages)
        self.build.signals.data.connect(self.buildData)
        self.build.signals.progress.connect(self.buildProg)
        self.build.signals.result.connect(self.buildResult)
        self.build.signals.error.connect(self.buildError)
        self.build.signals.finished.connect(self.buildDone)

        # init worker
        self.threadpool.start(self.build)

    def buildTheImages(self, data_callback, progress_callback):
        '''Build the images from the data entered

        Will start with the manager and follow with the nodes next to the manager ip

        The task is just to copy the base image and set on the address [TODO] a text file
        with this data:

            IP={nodeip}
            GW={gwip}
            DNS={dns}
            MODE={manager|node}
            MIP={managerip}

        And the rest of the image follows.
        '''

        baseIP = self.netGw[0:self.netGw.rfind('.') + 1]
        start = int(self.netManager[self.netManager.rfind('.') + 1:])
        end = start + int(self.netNodes) + 1
        count = end - start
        actual = 0
        overallProgress = 0
        singleProgress = 0
        fileSize = os.path.getsize(self.skybianFile)
        file = open(self.skybianFile, "rb")

        # main iteration cycle
        for n in range(start, end):
            # build node
            nip = baseIP + str(n)

            # actual node
            actual = n - start

            # create the config string
            ntype = 'manager' if nip == self.netManager else 'node'
            configText = "IP={0}\nGW={1}\nDNS='{2}'\nMODE={3}\nMIP={4}".format(nip, self.netGw, self.netDns, ntype, self.netManager)

            # fill the remaining space with null chars
            needToFill = imageConfigDataSize - len(configText)
            for i in range(0, needToFill):
                configText += "\x00"

            actualPosition = 0
            # WARNING! imageConfigAddress must be divisible by 4 for this to work ok
            portionSize = int(imageConfigAddress / 4)

            # new file and it's name
            nodeNick = "manager"
            if nip != self.netManager:
                nodeNick = "node" + str(actual)

            nodeName = "Skywire_your_" + nodeNick + ".img"

            nnfp = os.path.join(self.localPath, nodeName)
            newNode = open(nnfp, 'wb')
            nodes = int(self.netNodes)

            # user feedback
            data_callback.emit("Building node {}".format(nodeName))
            logging.debug("Building node {}, full path is:\n{}".format(nodeName, nnfp))

            # build node loop
            file.seek(actualPosition)
            while actualPosition < imageConfigAddress:
                data = file.read(portionSize)
                newNode.write(data)

                # progress and cycle update
                actualPosition += portionSize
                percent = actualPosition / fileSize

                overAll = percent/count + actual/count
                data = "Node creation {:.1%}|{:0.3f}".format(percent, overAll * 100)
                progress_callback.emit(percent * 100, data)

            # write config
            newNode.write(configText.encode())

            # seek to new position and resume the copy
            actualPosition += imageConfigDataSize
            file.seek(actualPosition)
            while actualPosition < fileSize:
                data = file.read(portionSize)
                newNode.write(data)

                # progress and cycle update
                actualPosition += portionSize
                percent = actualPosition / fileSize

                overAll = percent/count + actual/count
                data = "Node creation {:.1%}|{:0.1f}".format(percent, overAll * 100)
                progress_callback.emit(percent * 100, data)

            # close the newNode
            newNode.close()

        # close the file
        file.close()


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
        logging.debug("Unexpected error:", sys.exc_info()[0])
        raise
        sys.exit(-1)


