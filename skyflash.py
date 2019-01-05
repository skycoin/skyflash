#!/usr/bin/python3

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
skybianUrl = "http://192.168.200.1:8080/d.big"
# skybianUrl = "https://github.com/simelo/skyflash/issues/1"
manualUrl = "http://github.com/simelo/skyflash"

# utils class
class Utils(object):
    def __init__(self):
        return super(Utils, self).__init__()

    def shortenPath(self, fullpath, ccount):
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
        # takes int seconds to complete a task
        # return str like this
        #  < 10 seconds:  a few seconds
        #  > 10 seconds & < 1 minute: 45 seconds
        #  > 1 minute & < 59 minutes: 45 minutes
        #  > 1 hour: 1 hour 23 minutes

        # minutes to decide
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
        # takes speeds in bytes per second
        # return str like this
        #  < 1 kb/s: 256 b/s
        #  > 1 kb/s & < 1 Mb/s: 23 kb/s
        #  > 1 Mb/s: 2.1 Mb/s

        k = speed / 1000
        M = k / 1000
        out = ""

        if M > 1:
            out = "{:0.1f} Mb/s".format(M)
        elif k > 1:
            out = "{:0.1f} kb/s".format(k)
        else:
            out = "{} b/s".format(int(speed))

        return out


# signals class, to be used on threads; for all major tasks
class WorkerSignals(QObject):
    data = pyqtSignal(str)
    error = pyqtSignal(tuple)
    progress = pyqtSignal(float, str)
    result = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, parent=None):
        return super(WorkerSignals, self).__init__(parent=parent)


# Generic worker to use in threads
class Worker(QRunnable):
    
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

    ### init procedure
    def __init__(self, parent=None):
        return super(skyFlash, self).__init__(parent=parent)

    # download callbacks to emit signals to QML nd others
    def downloadSkybianData(self, data):
        self.dData.emit(data)

    def downloadSkybianProg(self, percent, data):
        self.dProg.emit(int(percent))
        self.setStatus.emit(data)

    def downloadSkybianError(self, error):
        # stop the download
        self.downloadActive = False
        self.dDown.emit()
        self.dData.emit("Download error...")
        self.setStatus.emit("An error ocurred, please check the network.")
        etype, eval, etrace = error
        print("An error ocurred:\n{}".format(eval))

    # result is the path to the local file
    def downloadSkybianFile(self, file):
        if self.downloadOk:
            self.skybianFile = file
            # TODO adjust the size of the path
            self.dData.emit("Skybian image is: " + utils.shortenPath(file, 32))
            self.setStatus.emit("Choose your network configuration")
        else:
            self.dData.emit("Download canceled or error")
            self.setStatus.emit("Download canceled or error happened")
            self.dDown.emit()

    # download finished, good or bad?
    def downloadSkybianDone(self, result):
        # check status of download
        if self.downloadOk:
            self.dDone.emit()
            self.netConfig.emit()

    # Download main trigger
    @pyqtSlot()
    def downloadSkybian(self):
        # check if there is a thread already working there
        downCount = self.threadpool.activeThreadCount()
        if downCount < 1:
            # rise flag
            self.downloadActive = True

            # set label to starting
            self.dData.emit("Download starting...")

            # init download process
            self.down = Worker(self.skyDown)
            self.down.signals.data.connect(self.downloadSkybianData)
            self.down.signals.progress.connect(self.downloadSkybianProg)
            self.down.signals.result.connect(self.downloadSkybianFile)
            self.down.signals.error.connect(self.downloadSkybianError)
            self.down.signals.finished.connect(self.downloadSkybianDone)

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

        self.size = int(req.info()['Content-Length'])
        fileName = url.split("/")[-1]

        # emit data of the download
        data_callback.emit("Downloading {:04.1f} MB".format(self.size/1000/1000))

        # start download
        downloadedChunk = 0

        # chuck size @ 100kb
        blockSize = 102400
        # TODO folder separator can be os depenndent, review
        filePath = os.getcwd() + "/" + fileName
        startTime = 0
        elapsedTime = 0

        # DEBUG
        print("Downloading to: {}".format(filePath))

        try:
            with open(filePath, "wb") as finalImg:
                startTime = time.time()
                while True:
                    chunk = req.read(blockSize)
                    if not chunk:
                        print("\nDownload Complete.")
                        break
                    downloadedChunk += len(chunk)
                    finalImg.write(chunk)
                    progress = (float(downloadedChunk) / self.size) * 100

                    # calc speed and ETA
                    elapsedTime = time.time() - startTime
                    bps = int(downloadedChunk/elapsedTime) # b/s
                    etas = int((self.size - downloadedChunk)/bps) # seconds
                    # emit progress
                    prog = "{:.1%}, {}, {} to go.".format(progress/100,  utils.speed(bps), utils.eta(etas))
                    progress_callback.emit(progress, prog)

                    # check if the terminate flag is raised
                    if not self.downloadActive:
                        finalImg.close()
                        return "canceled"

            # close the file handle
            finalImg.close()
            self.downloadOk = True

            # return the local filename
            return filePath

        except:
            self.downloadOk = False
            if finalImg:
                finalImg.close()
                os.unlink(finalImg)

            return "Abnormal termination"

    # load skybian from a local file
    @pyqtSlot(str)
    def localFile(self, file):
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
        self.downloadSkybianFile(file)
        self.downloadSkybianDone("Ok")

    # open the manual in the browser
    @pyqtSlot()
    def openManual(self):
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

