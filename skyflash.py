#!/usr/bin/python3

from PyQt5.QtGui import QGuiApplication
# from PyQt5.QtWidgets import QApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import QObject, QUrl, pyqtSlot, pyqtSignal
import os, sys, subprocess, webbrowser

# environment vars
skybianUrl = "http://localhost:8080/skybian.tar.xz"
manualUrl = "http://github.com/simelo/skyflash"

# utils classs
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


# main object definition
class skyFlash(QObject):
    def __init__(self):
        QObject.__init__(self)
        bimg = ""

    # registering Signals to emit to QT-QML
    downloadUpdate = pyqtSignal(int, arguments=["percent"])
    downloadFinished = pyqtSignal(str, arguments=["msg"])
    setStatus = pyqtSignal(str, arguments=["msg"])


    @pyqtSlot()
    def downloadSkybian(self):
        # get default URL for downloads
        Url = skybianUrl

        # DEBUG
        print("Entrando a download...")

        # some validation
        if Url is "" or "http" not in Url:
            self.setStatus.emit("URL is empty or mangled, please check")

        # set status
        self.setStatus.emit("Starting the download from the official site")
        self.downloadFinished.emit("/tmp/Skybian-1.0.img")


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


    @pyqtSlot(str)
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
        

app = QGuiApplication(sys.argv)
# app = QApplication(sys.argv)
skyflash = skyFlash()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("skf", skyflash)
engine.load("skyflash.qml")
engine.quit.connect(app.quit)

# instance of utils
utils = Utils()

if __name__ == "__main__":
    try:
        sys.exit(app.exec_())
    except:
        sys.exit("Ooops!")

