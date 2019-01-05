#!/usr/bin/python3

# main imports
import os
import sys
import subprocess
import webbrowser
from urllib.request import Request, urlopen

# GUI imports
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import *

# environment vars
# TODO, set final real URLS
skybianUrl = "http://127.0.0.1:8080/d.big"
manualUrl = "http://github.com/simelo/skyflash"

# utils class
class Utils(object):
    def __init__(self):
        return super(Utils, self).__init__()

    def shortenPath(self, fullpath, ccount):
        # TODO OS dependent FS char
        fpath = fullpath.split("/")
        spath = fpath[-1]
        if len(spath) > ccount:
            spath = ".../" + spath[-ccount:]
        else:
            spath = ".../" + spath

        return spath


# signals class, to be used on threads; for all major tasks
class WorkerSignals(QObject):
    data = pyqtSignal(str)
    error = pyqtSignal(tuple)
    progress = pyqtSignal(int)
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
            self.signals.finished.emit()


# main object definition
class skyFlash(QObject):
    #### registering Signals to emit to QML GUI

    # status bar
    setStatus = pyqtSignal(str, arguments=["msg"])

    # download signals
    dData = pyqtSignal(str, arguments=["data"])
    dProg = pyqtSignal(float, arguments=["percent"])
    dDone = pyqtSignal(str, arguments=["result"])

    # thread pool
    threadpool = QThreadPool()

    ### init procedure
    def __init__(self, parent=None):
        return super(skyFlash, self).__init__(parent=parent)

    # download callbacks to emit signals to QML nd others
    def downloadSkybianData(self, data):
        self.dData.emit(data)

    def downloadSkybianProg(self, percent):
        self.dProg.emit(percent)

    def downloadSkybianError(self, error):
        print("Error: " + error)

    def downloadSkybianFile(self, file):
        self.skybianFile = file

    def downloadSkybianDone(self, result):
        self.dDone.emit(result)

    # Download main trigger
    @pyqtSlot()
    def downloadSkybian(self):
        # check if there is a thread already working there
        downCount = self.threadpool.activeThreadCount()
        if downCount < 1:
            # init download process
            self.down = Worker(self.skyDown)
            self.down.signals.data.connect(self.downloadSkybianData)
            self.down.signals.progress.connect(self.downloadSkybianProg)
            self.down.signals.result.connect(self.downloadSkybianFile)
            self.down.signals.finished.connect(self.downloadSkybianDone)

            # init worker
            self.threadpool.start(self.down)
        else:
            # TODO, emit status bar warning or modal box
            print("There is a download in progress, please wait...")

    # download skybian, will be instantiated in thread
    def skyDown(self, data_callback, progress_callback):
        # take url for skybian from upper
        url = skybianUrl

        print("Downloading from: {}".format(url))
        r = Request(url)
        req = urlopen(r)
        self.size = int(req.info()['Content-Length'])
        fileName = url.split("/")[-1]

        # emit data of the download
        data_callback.emit("~" + str(self.size/1000) + "MB" )

        # start download
        downloadedChunk = 0

        # chuck size @ 20kb
        blockSize = 20480 
        localFile = os.getcwd() + fileName

        # DEBUG
        print("Downloading to: {}".format(localFile))

        with open(localFile, "wb") as finalImg:
            while True:
                chunk = req.read(blockSize)
                if not chunk:
                    print("\nDownload Complete.")
                    break
                downloadedChunk += len(chunk)
                finalImg.write(chunk)
                progress = float(downloadedChunk) / self.size
                
                # emit percent
                progress_callback.emit(progress * 100)

        # final emit
        print("Done")

        # close the file handle
        finalImg.close()

        # return the local filename
        return localFile

    # load skybian from a local file
    @pyqtSlot()
    def localFile(self, file):
        if file is "":
            self.setStatus.emit("You selected nothing, plase try again")
            return
        
        if file.startswith("file://"):
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

        # shorten the filename to fit on the label
        filename = utils.shortenPath(file, 26)
        self.downloadFinished.emit(filename)

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

