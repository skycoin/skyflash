#!/usr/bin/env python3

# main imports
import os
import sys
import subprocess
import webbrowser
import time
import traceback
import ssl
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
    """This is a basic class to hold procedures & functions that does not belongs
    to any other part or class in the project, such as validation, conversion, 
    formatting, etc. As the name implies a utils tool box"""

    def __init__(self):
        return super(Utils, self).__init__()

    def shortenPath(self, fullpath, ccount):
        """Shorten a passed FS path to a char count size"""

        # TODO OS dependent FS char
        fpath = fullpath.split("/")
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
                # TODO OS dependant FS char
                tspath = item + "/" + spath
                if len(tspath) > ccount:
                    spath = ".../" + spath
                    break
                else:
                    spath = tspath

        # spath has the final shorted path
        return spath

    def eta(self, secs):
        """Format a second time span in a text human readable representation
        returned as a string, for example:

        secs < 10 seconds:  "a few seconds"
        secs > 10 seconds & < 1 minute: "{secs} seconds"
        secs > 1 minute & < 59 minutes: "{min} minutes"
        secs > 1 hour: "{} hour {} minutes"
        """

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
        """Takes a bytes per second speeds and returns a string with a human readable
        representation of that speed, such as:

        speed < 1 KB/s: "{} b/s"
        speed > 1 KB/s & < 1 MB/s: "{} KB/s"
        speed > 1 MB/s: {} MB/s
        """

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
        """Takes a byte size and return it as a human readable string,
        such as this:
        
        size < 1 KB: "{} bytes"
        size > 1 KB & < 1 MB:  "{0.3f} KB"
        size > 1 MB: "{0.3f} MB"
        """

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


# signals class, to be used on threads; for all major tasks
class WorkerSignals(QObject):
    """This class defines the signals to be emmited by the different threaded
    proseses that will be run on this soft"""

    data = pyqtSignal(str)
    error = pyqtSignal(tuple)
    progress = pyqtSignal(float, str)
    result = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, parent=None):
        return super(WorkerSignals, self).__init__(parent=parent)


# Generic worker to use in threads
class Worker(QRunnable):
    """This is the way we manage threads, not by QThread, but a QRunner
     inside a thread pool, in this way we use a generic runable procedure
     of the main object and not a object itself, easy to manage & stable
     """

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
        """This is the main procedure that runs in the thread pool"""

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
    """Main/Base object for all procedures and properties, this is the core
    of our App
    """

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
    # target is download button text: Download
    dDown = pyqtSignal()

    # download flags
    downloadActive = False
    downloadOk = False

    # network signals
    netConfig = pyqtSignal()

    # thread pool
    threadpool = QThreadPool()

    # files handling vars
    downloadFileSize = 0
    donwloadedFile = ""
    skybianFile = ""

    ### init procedure
    def __init__(self, parent=None):
        return super(skyFlash, self).__init__(parent=parent)

    # download callbacks to emit signals to QML nd others
    def downloadFileData(self, data):
        """Update the label beside the buttons in the download box on the UI"""

        self.dData.emit(data)

    def downloadFileProg(self, percent, data):
        """Update the progress bar and status bar about the task progress"""

        self.dProg.emit(percent)
        self.setStatus.emit(data)

    def downloadFileError(self, error):
        """Stop the threaded task and produce feedbak to the user"""

        # stop the download
        self.downloadActive = False
        self.dDown.emit()
        self.dData.emit("Download error...")
        self.setStatus.emit("An error ocurred, please check the network.")
        etype, eval, etrace = error
        print("An error ocurred:\n{}".format(eval))

    # result is the path to the local file
    def downloadFileResult(self, file):
        """Receives the result of the download: the path to the downloaded file """

        if self.downloadOk:
            self.donwloadedFile = file
            # TODO adjust the size of the path
            self.dData.emit("Skybian compressed file is: " + utils.shortenPath(file, 32))
        else:
            self.dData.emit("Download canceled or error")
            self.setStatus.emit("Download canceled or error happened")
            self.dDown.emit()

    # download finished, good or bad?
    def downloadFileDone(self, result):
        """End of the download task"""

        # check status of download
        if self.downloadOk and self.donwloadedFile != "":
            self.dDone.emit()
            
            # call to handle the download (a img or a compressed one)
            self.downloadProcess()

    # Download main trigger
    @pyqtSlot()
    def downloadSkybian(self):
        """Slot that receives the stat download signal from the UI"""

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
        """Download task, this will runs in a threadpool"""

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
        # TODO folder separator can be os dependent, review
        filePath = os.getcwd() + "/" + fileName
        startTime = 0
        elapsedTime = 0

        # DEBUG
        print("Downloading to: {}".format(filePath))

        try:
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
                        return "canceled"

            # close the file handle
            downFile.close()
            self.downloadOk = True

            # return the local filename
            return filePath

        except:
            self.downloadOk = False
            if downFile:
                downFile.close()
                os.unlink(downFile)

            return "Abnormal termination"

    # load skybian from a local file
    @pyqtSlot(str)
    def localFile(self, file):
        """Slot that receives the local folder picked up to process"""

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

        # all seems good, emit ans go on
        self.downloadOk = True
        self.downloadFileDone("Ok")
        self.downloadFileResult(file)

    # process a local picked file or a downloaded one
    def downloadProcess(self):
        """Process a downloaded/locally picked up file, it can be a .img or a
        .tar.[gz|xz] one.
        
        If a compressed must decompress and check sums to validate and/or
        if a image must check for a fingerprint to validate
        
        If error produce feedback, if ok, continue.
        """
        
        print("must process the downloade file, I know...")

        pass


    # open the manual in the browser
    @pyqtSlot()
    def openManual(self):
        """Opens the manual in a users's default browser"""

        if sys.platform == "win32":
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


if __name__ == "__main__":
    """Run the script"""

    try:
        # instance of utils
        utils = Utils()

        app = QGuiApplication(sys.argv)
        # app = QApplication(sys.argv)
        skyflash = skyFlash()
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("skf", skyflash)
        engine.load("skyflash.qml")
        engine.quit.connect(app.quit)

        # main GUI call
        sys.exit(app.exec_())
    except:
        sys.exit("Ooops!")

