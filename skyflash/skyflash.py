# main object definition

# main imports
import os
import io
import sys
import webbrowser
import time
import tarfile
import ssl
import hashlib
import logging
import subprocess
import enum
import string
import tempfile
import time
import configparser
from urllib.request import Request, urlopen

# GUI imports
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import QThreadPool, QTimer, pyqtProperty

# New imports
from skyflash.utils import *

# image config file position and size
imageConfigAddress = 12582912
imageConfigDataSize = 256

# skybian URL
defaultSkybianUrl = "https://github.com/skycoin/skybian/releases/download/Skybian-v0.0.4/Skybian-v0.0.4.tar.xz"
readmeUrl = "https://github.com/skycoin/skyflash/blob/master/README.md#installing-or-upgrading"
manualUrl = "https://github.com/skycoin/skyflash/blob/master/USER_MANUAL.md"

class Skyflash(QObject):
    '''Main/Base object for all procedures and properties, this is the core
    of our App
    '''

    # Variables
    downloadActive = False
    downloadOk = False
    downloadSize = 0
    downloadedFile = ""
    skybianFile = ""
    extractionOK = False
    digestAlgorithm = ""
    digest = ""
    localPathDownloads = ""
    localPath = ""
    localPathBuild = ""
    config = configparser.ConfigParser()
    config_file = ""
    netGw = ""
    netDns = ""
    netManager = ""
    netNodes = ""
    cksumOk = False
    cardList = []
    card = ""
    drives = []
    builtImages = []
    flashingNow = []
    flashingOnProgress = False
    appFolder = ""
    bundle = False
    skybianUrl = ""
    skybianUpdated = False # true: updated, false: not, none tried but failed

    #### registering Signals to emit to QML GUI

    # status bar
    setStatus = pyqtSignal(str, arguments=["msg"])

    #### QT QML signals

    ## Dialog signals

    # target is okDialog Box rise
    uiOk = pyqtSignal(str, str, arguments=["title", "text"])
    # target is warnDialog Box rise
    uiWarning = pyqtSignal(str, str, arguments=["title", "text"])
    # target is errorwarnDialog Box rise
    uiError = pyqtSignal(str, str, str, arguments=["title", "text", "details"])
    # target is errorwarnDialog Box rise
    uiNewVersion = pyqtSignal()

    ## image related signals

    # target is download label
    dData = pyqtSignal(str, arguments=["data"])
    # target is proogress bar
    dProg = pyqtSignal(float, arguments=["percent"])
    # target is hide download buttons
    dDone = pyqtSignal()
    # target is show download buttons and reset the whole UI
    sStart = pyqtSignal()
    # target is show download buttons as ready to download
    sDB = pyqtSignal()

    ## Signals related to the build process

    # build data, show a hint to the users
    bData = pyqtSignal(str, arguments=["data"])
    # build single process show single file build progress
    bsProg = pyqtSignal(float, arguments=["percent"])
    # build overall progress, show overall progress for the whole image build
    boProg = pyqtSignal(float, arguments=["percent"])
    # hide the progress bars after the built is done, and show Flash box
    bFinished = pyqtSignal()
    #
    # signal to show the default path and let the user pick his own
    bDestinationDialog = pyqtSignal(str, arguments=["folder"])
    # signal to update the network data
    bNetData = pyqtSignal(str, str, str, str, arguments=["gw", "dns", "manager", "nodes"])

    ## Signals related to the flash process

    # warn the UI that the list of cards has been changed
    cardsChanged = pyqtSignal()
    # warn the UI that the list of images has been changed
    builtImagesChanged = pyqtSignal()
    # flash process show
    fsProg = pyqtSignal(float, arguments=["percent"])

    # download flags
    downloadActive = False
    downloadOk = False

    # files handling vars
    downloadSize = 0
    downloadedFile = ""
    skybianFile = ""
    skybianFileVersion = ""

    # extraction flags
    extractionOk = False

    # checksum vars
    cksumOk = False

    # network signals
    netConfig = pyqtSignal()
    netDefaultBox = pyqtSignal(bool, arguments=["status"])
    buildImages = pyqtSignal()

    # thread pool
    threadpool = QThreadPool()

    # timer or card detection
    timer = QTimer()

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
        self.resetWorkspace()

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
            self.resetWorkspace()

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

            # logs
            logging.debug("Downloaded file is {}".format(self.downloadedFile))

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
        self.resetWorkspace()

        # specific feedback
        self.setStatus.emit("Please try again")
        etype, eval, etrace = error
        logging.debug("An error ocurred:\n{}".format(eval))
        self.uiError.emit("Extraction error", "There was an error extracting the downloaded file, this is mainly due to a corrupted download, please try again.", str(eval))

    # cksum ones

    def cksumResult(self, result):
        '''Callback that receives the signal for a cksum finished, an
        argument is passed, result, it's true or false to flag success or failure'''

        # debug
        logging.debug("Checksum verification result: {}".format(result))

        # name of the downloaded file
        filename = self.skybianFile.split(os.path.sep)[-1]

        if result:
            self.cksumOk = True
            self.dData.emit("{} base image verified!".format(filename))
            logging.debug("Checksum verification result is ok")
        else:
            self.cksumOk = False
            self.dData.emit("Flash file {} can't be verified!".format(filename))
            logging.debug("Checksum verification failed: hash differs!")
            self.uiError.emit("Flash file {} can't be verified!", "The Skybian image integrity check ended with a different fingerprint or a soft error, this image is corrupted or a soft error happened, please start again.", "Downloaded & computed Hash differs".format(filename))

    def cksumDone(self):
        '''Callback that is flagged once the checksum was ended.'''

        # debug
        logging.debug("Checksum verification done")

        if self.cksumOk:
            # success must call for a sha1sum check
            logging.debug("Checksum verification success!")
            # next step
            self.skybianFileVersion = self.getSkybianVersion(self.skybianFile)
            self.netConfig.emit()
            self.buildImages.emit()

            # set the config items and save them
            self.config['MAIN']['setup'] = 'yes'
            self.config['SKYBIAN']['verified'] = 'yes'
            self.config['SKYBIAN']['file'] = self.skybianFile
            self.config['SKYBIAN']['version'] = self.skybianFileVersion
            self.save_config()

            # check if there are old files and clean it up
            eraseOldVersions(self.localPathDownloads, self.skybianFileVersion)
        else:
            # error in the checksum process is not handled here, just at the end of the checksum, see cksumError for process errors

            # cksum failed
            self.config['SKYBIAN']['setup'] = 'no'
            self.config['SKYBIAN']['file'] = ''
            self.config['SKYBIAN']['version'] = ''
            self.save_config()

    def cksumError(self, error):
        '''Process the error of the checksum, this only process error in the
        process, a completed checksum but not matching is handled by result
        not in this.
        '''

        # stop the extraction & reset env
        self.resetWorkspace()

        # specific feedback
        self.dData.emit("Checksum process error...")
        self.setStatus.emit("An error ocurred, can't do the image verification")
        etype, eval, etrace = error
        logging.debug("An error ocurred while verifying the checksum:\n{}".format(eval))
        self.uiError.emit("Integrity check failed!", "The Skybian image integrity check failed with an error, please check the logs to see more details", str(eval))

    # build ones

    def buildData(self, data):
        '''Pass a test string to the label nex to the Build Images button'''

        self.bData.emit(data)

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

    def buildError(self, error):
        '''Catch any error on the image build process and pass it to the user'''

        self.dData.emit("Build process error...")
        self.setStatus.emit("An error ocurred, can't build the images")
        etype, eval, etrace = error
        logging.debug("An error ocurred while building the images:\n{}".format(eval))
        self.uiError.emit("Build failed!", "The build process failed, please check the logs to see more details", str(eval))

    def buildDone(self, data):
        '''Catch the end of the build process

        Congrats to the user and suggestion to use the burn option
        (or use your preferred flasher for the task)
        '''

        self.setStatus.emit("Images build was a success, next step is flashing!")
        self.bData.emit("All images were built")
        self.bFinished.emit()
        # check for cards timer start
        self.timerStart()

        # config update
        self.config['MAIN']['setup'] = 'yes'
        self.save_config()

    # flash ones

    def flashProg(self, percent, data):
        '''Update two progressbar and a status bar in the UI

        The data is to update the status bar
        '''

        # split data
        self.fsProg.emit(percent)
        self.setStatus.emit(data)

    def flashResult(self, data):
        ''''''

        # restart the timer
        self.timerStart()

        pass

    def flashError(self, error):
        '''Catch any error on the image flash process and pass it to the user'''

        # restart the timer
        self.timerStart()
        self.setStatus.emit("An error ocurred while flashing the images")
        etype, eval, etrace = error
        logging.debug("An error ocurred while flashing the images:\n{}".format(eval))
        self.uiError.emit("Flash failed!", "The flash process failed, please check the logs to see more details", str(eval))

        # reset the fail safe trigger
        self.flashingOnProgress = False

    def flashDone(self, data):
        '''Catch the end of the flash process'''

        # restart the timer
        self.timerStart()

        # user feedback
        msg = """Congratulations, you have flashed it successfully!
To flash the next image just follow these steps:
  1. Remove the actual card from your PC
  2. Insert the next node card into the slot
  3. Pick the proper device in the combo box
  4. Pick the next desired image from the combo box 
  5. Click the Flash button and wait until it finish"""  
        self.uiOk.emit("Image flashing succeeded!", msg)

        self.setStatus.emit("Flash process was a success!")

        # reset the fail safe trigger
        self.flashingOnProgress = False

        # config update
        self.config['MAIN']['setup'] == 'yes'
        self.save_config()

    def checkUpdatesResult(self, data):
        '''Receive the result of the check for updates via data

        data is a string either: Null, False or True

        Null indicate that we can't reach the update server (ignore, will check on next try)
        False indicate it checked and you has the latest version
        True indicates you are in a old version
        '''

        logging.debug("Check for skyflash updates result: {}".format(data))

        if data == "True":
            # we have a explicit difference, warn the user; then open the manual
            self.uiNewVersion.emit()

    @pyqtSlot()
    def openUpdateLink(self):
        '''Open the Link to the online manual in the readme url'''

        self.openManual(readmeUrl)

    def getSkybianVersion(self, data):
        '''Get he version of a Skybian image by it's name

        You can pass either a image or a release file

        Image:   Skybian-v0.0.4.img
        Release: Skybian-v0.0.4.tar.xz

        With the provision to strip the pat is it's a URL, or a FS path
        it must return something like "v0.0.4"
        '''

        # DEBUG
        logging.debug("Get he version from a data line, in this case:\n{}".format(data))

        sfile = ''

        # detect if a url
        if data.startswith('https'):
            # DEBUG
            logging.debug("Passed data is an URL")

            # check it the URL ends with a '/' and strip it, shit happens
            if data[-1] is '/':
                data = data[:-1]

            sfile = data.split('/')[-1]
        else:
            # DEBUG
            logging.debug("Passed data is not an URL")

            # detect if we need to split the path
            if os.path.sep in data:
                # DEBUG
                logging.debug("Passed data is FS path")
                spath = data.split(os.path.sep)
                if len(spath) >= 2:
                    sfile = spath[-1]
            else:
                sfile = data

        # DEBUG
        logging.debug("At this point we get the filename only: {}".format(sfile))

        # parse the file, some like this: Skybian-v0.0.4.tar.xz or Skybian-v0.0.4.img
        if 'img' in sfile:
            name = '.'.join(sfile.split('.')[:-1])
        else:
            name = '.'.join(sfile.split('.')[:-2])

        ver = name.split('-')[1]

        # DEBUG
        logging.debug("Version is {}".format(ver))

        return ver

    def skybianUrlResult(self, data):
        '''Receive the result of the fetch for the latest skybian URL

        data is a string either: the url for the download or a error message
        '''

        if self.skybianUpdated == False:
            # check for it
            logging.debug("Got an answer to the skybian URL update:\n{}".format(data))

            # check if a valid url
            if data.startswith("https"):
                # valid
                self.skybianUpdated = True
                self.skybianUrl = data
                self.setStatus.emit("Skybian download source updated...")
                self.sDB.emit()
                logging.debug("Skybian download source updated...")

                # if it's a new version erase local one and restart the UI
                if self.skybianFileVersion is not '' and self.skybianFile is not '':
                    # we have a local version, get url version
                    skbURLVer = self.getSkybianVersion(data)

                    # if a new version alert the user and reset the interface
                    if skbURLVer != self.skybianFileVersion:
                        self.uiWarning.emit("New version of Skybian", "We have detected a new version of Skybian, please download the new version")
                        eraseOldVersions(self.localPathDownloads, "---")
                        self.sStart.emit()
            else:
                # tried but failed
                self.skybianUpdated = None
                self.setStatus.emit("Can't fetch the Skybian download source")
                logging.debug("Can't fetch the Skybian download source")

        elif self.skybianUpdated == None:
            # tried to update for the second time, using the default
            self.skybianUpdated = True # fake true
            self.skybianUrl = defaultSkybianUrl # recall the latest download knows to the app
            self.setStatus.emit("Using the default Skybian download source")
            logging.debug("Using the default Skybian download source")
        else:
            # already
            logging.debug("Skybian URL already updated...")

    @pyqtSlot()
    def downloadSkybian(self):
        '''Slot that receives the start download signal from the UI'''

        # check to see if we got the skybian download URL
        if self.skybianUpdated == False:
            # call for an update
            self.updateSkybianURL()

            # update the status bar
            self.setStatus.emit("Fetching the download link... are you Online?")

            return

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
            self.sStart.emit()

    # download skybian, will be instantiated in a thread
    def skyDown(self, data_callback, progress_callback):
        '''Download task, this will runs in a threadpool

        Result returned must be string and in this case will be the
        path for the downloaded file or an empty string on error/cancel

        This method is wrapped by the thread and will catch any errors
        upstream so no need to handle it here
        '''

        # get the URL from the object
        url = self.skybianUrl

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
            data_callback.emit("{}, {:04.1f} MB".format(fileName, self.downloadSize/1000/1000))
        else:
            data_callback.emit("Downloading {}...".format(fileName))

        # start download
        downloadedChunk = 0

        # chuck size @ 100KB
        blockSize = 102400
        filePath = os.path.join(self.localPathDownloads, fileName)
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
                    prog = "{:.1%}, {}, {} to go".format(progress/100,  speed(bps), eta(etas))
                else:
                    prog = "{} so far at {}, unknown ETA".format(size(downloadedChunk),  speed(bps))

                # emit progress
                progress_callback.emit(progress, prog)

                # check if the terminate flag is raised
                if not self.downloadActive:
                    downFile.close()
                    os.unlink(filePath)
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
        if 'nt' in os.name:
            # file is like this file:///C:/Users/Pavel/Downloads/Skybian-0.1.0.tar.xz
            # need to remove 3 slashes
            file = file.replace("file:///", "")
        else:
            # working on posix, like this: file:///home/pavel/Downloads/Skybian-0.1.0.tar.xz
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
        time.sleep(1)
        self.downloadFileDone("OK")

    def downloadProcess(self):
        '''Process a downloaded/locally picked up file.

        If a compressed must decompress and check sums to validate

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
        os.chdir(self.localPathDownloads)

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
        filename = self.downloadedFile.split(os.path.sep)[-1]
        data_callback.emit("Extracting the file {}, please wait...".format(filename))
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
    def openManual(self, url=manualUrl):
        '''Opens the manual in a users's default browser'''

        logging.debug("Trying to open the manual page (or readme) on the browser, wait for it...")

        if sys.platform in ["win32", "cygwin"]:
            try:
                os.startfile(url)
            except:
                webbrowser.open(url)

        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])

        else:
            try:
                subprocess.Popen(["xdg-open", url])
            except OSError:
                logging.debug("Please open a browser on: " + url)

    def cleanFolder(self, path):
        '''Cleans the passed folder of any temp/work file, covered files to erase
        are the ones in the filePatterns list
        '''

        logging.debug("Clean of folder {} called".format(path))

        # list of file extensions to erase
        filePatterns = ["img", "gz", "xz", "sha1", "md5"]

        for item in os.listdir(path):
            itemExtension = item.split(".")[-1]
            if itemExtension in filePatterns:
                logging.debug("Erasing file {}".format(item))
                os.unlink(path + "/" + item)

    def resetWorkspace(self):
        '''Reset the workspace, erase any temp/work file and resets the
        interface to start all over again like a fresh start, erasing
        vars from the previous run'''

        logging.debug("Reset workspace called, cleaning the house")

        # clean work folder
        self.cleanFolder(self.localPath)

        # clean build folder
        self.cleanFolder(self.localPathBuild)

        # clean download folder
        self.cleanFolder(self.localPathDownloads)

        # vars reset
        self.downloadedFile = ""
        self.downloadOk = False
        self.downloadActive = False
        self.skybianFile = ""
        self.extractionOk = False

        # GUI reset
        self.sStart.emit()

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
        files = os.listdir(self.localPathDownloads)
        for file in files:
            ext = file.split(".")[-1]
            if ext in digestAlgorithms:
                logging.debug("Found checksum file: {}".format(file))
                digestFile = os.path.join(self.localPathDownloads, file)
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
        imgFile = os.path.join(self.localPathDownloads, imgFile.strip("*"))
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

        logfile = os.path.join(self.localPath, "skyflash.log")
        logging.basicConfig(filename=logfile, level=logging.DEBUG)

        logging.info("")
        logging.info("====================================================")
        logging.info("Logging started at {}".format(time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())))
        logging.info("====================================================")
        logging.info("")

    def timerStart(self):
        '''Start the timer to check for SD cards'''

        try:
            self.timer.timeout.connect(self.detectCards)
        except:
            pass

        # timer stopped, not started until step 4 is visible
        self.timer.start(1000)

    def timerStop(self):
        '''Stop the timer to check for SD cards'''
        try:
            self.timer.stop()
        except:
            pass

    def validateNetworkData(self, dgw, ddns, dmanager, dnodes, ui=True):
        '''Validate the network data passed by the QML UI

        gw: the network gateway
        dns: the DNS to use in the format "1.2.3.4, 4.3.2.1" (must pass it along as is)
        manager: ip of the manager
        nodes: number of nodes to build

        The input vars is prefixed by a 'd' to sign they can be dirty with
        leading or trailing spaces, comas or dots

        If all data is good, clean values are passed to the UI via a signal

        Returns true or false to sign result
        '''

        # removing trailing and leading spaces
        gw = cleanString(dgw)
        dns = cleanString(ddns)
        manager = cleanString(dmanager)
        nodes = cleanString(dnodes)

        # debug
        logging.debug("Build received data is:\nGW: '{}'\nDNS: '{}'\nManager: '{}'\nNodes '{}'".format(gw, dns, manager, nodes))

        # validation #1, are the manger & gw valid ips?
        gwValid, reason = validIP(gw)
        if not gwValid:
            if ui:
                self.uiError.emit("Validation error", "The GW IP entered is not valid, please check that", reason)
            logging.debug("GW ip not valid: {}".format(gw))
            return False

        managerValid, reason = validIP(manager)
        if not managerValid:
            if ui:
                self.uiError.emit("Validation error", "The Manager IP entered is not valid, please check that", reason)
            logging.debug("Manager ip not valid: {}".format(manager))
            return False

        # validation #2, DNS
        # from 1 to 3 IPs separated by ',' or space, or both
        ddns = splitDNS(dns)
        if ddns[0] == False:
            if ui:
                reason = "DNS must be in the format '1.2.3.4, 2.3.4.5, 3.4.5.6'"
                self.uiError.emit("Validation error",
                              "The DNS string entered is not valid, please check that.",
                              reason)
            logging.debug("DNS string is not valid: '{}'".format(dns))
            return False

        # validation #3, gw and manager must be on the same IP range
        if gw[0:gw.rfind('.')] != manager[0:manager.rfind('.')]:
            if ui:
                self.uiError.emit("Validation error",
                              "The manager and the gw are not in the same sub-net, please check that",
                              "Manager and Gateway must reside on the name subnet")
            logging.debug("Base address for the net differs in gw/manager: '{} vs. {}'".format(gw, manager))
            return False

        # validation #4, node counts + ip is not bigger than 255
        endip = int(manager[manager.rfind('.') + 1:]) + int(nodes)
        if endip >= 255:
            if ui:
                self.uiError.emit("Validation error",
                              "The nodes IP distribution is beyond 254, please lower your manager ip",
                              "The IP of the nodes are distributed from the manager IP and up, if you set the manager node IP so high the node count may not fit")
            logging.debug("Manager IP to high, last node will be {} and that's not possible".format(endip))
            return False

        # validation #5, gw not in manager & nodes range
        if int(gw[gw.rfind('.') + 1:]) in range(int(manager[manager.rfind('.') + 1:]), endip):
            if ui:
                self.uiError.emit("Validation error",
                              "Please check your GW, Manager & Nodes selection, the GW is one of the Nodes or Manager IPs",
                              "When we distribute the manager & nodes IP we found that the GW is one of that IP and that's wrong")
            logging.debug("GW ip is on generated nodes range.")
            return False

        # If you reached this point then all is ok
        # Push the new data to the UI
        self.bNetData.emit(gw, dns, manager, nodes)

        # finally return true
        return True

    @pyqtSlot(str, str, str, str)
    def builtImagesPath(self, gw, dns, manager, nodes):
        '''Receives the info from the UI that the user want to build the images
        and the parameters to do it.

        We validate the data on the users interface first, if somethins is wrong
        we raise an error dialog.

        Then ask to the user if it's OK with the location, if not then raise a
        dialog box to select the new path
        '''

        # validate network data
        result = self.validateNetworkData(gw, dns, manager, nodes)
        if not result:
            return

        self.bDestinationDialog.emit(self.localPathBuild)

    @pyqtSlot(str, str, str, str, str)
    def imagesBuild(self, gw, dns, manager, nodes, folder):
        '''Receives the Button order to build the images, passed arguments are:

        gw: the network gateway
        dns: the DNS to use in the format "1.2.3.4, 4.3.2.1" (must pass it along as is)
        manager: ip of the manager
        nodes: number of nodes to build

        It uses that data to run a network info validation and the proceed if needed 
        '''

        # run validations
        result = self.validateNetworkData(gw, dns, manager, nodes)
        if not result:
            return

        # clean the path depending on the OS
        if 'nt' in os.name:
            # file is like this file:///C:/Users/...
            # need to remove 3 slashes
            folder = folder.replace("file:///", "")
        else:
            # working on posix, like this: file:///home/pavel/...
            folder = folder.replace("file://", "")

        if folder != "no":
            # change it
            self.localPathBuild = folder
            logging.debug("User selected a custom build folder: {}".format(self.localPathBuild))

        # erase old images on final folder (if any)
        self.cleanFolder(self.localPathBuild)

        # All good carry on, set the network vars on top of the object
        self.netGw = gw
        self.netDns = dns
        self.netManager = manager
        self.netNodes = nodes

        # push the values oin the config
        self.config['NET']['configured'] = 'yes'
        self.config['NET']['gw'] = gw
        self.config['NET']['dns'] = dns
        self.config['NET']['manager'] = manager
        self.config['NET']['count'] = nodes
        self.save_config()

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
        images = []
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
                nodeNick = "node-" + str(actual)

            nodeName = "Skybian-" + nodeNick + ".img"

            nnfp = os.path.join(self.localPathBuild, nodeName)
            newNode = open(nnfp, 'wb')
            nodes = int(self.netNodes)

            # user feedback
            data_callback.emit("Building {} image".format(nodeNick))
            logging.debug("Building {} image, full path is:\n{}".format(nodeName, nnfp))

            # build node loop
            file.seek(actualPosition)
            while actualPosition < imageConfigAddress:
                data = file.read(portionSize)
                newNode.write(data)

                # progress and cycle update
                actualPosition += portionSize
                percent = actualPosition / fileSize

                overAll = percent/count + actual/count
                data = "Image creation {:.1%}|{:0.3f}".format(percent, overAll * 100)
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
                data = "Image creation {:.1%}|{:0.1f}".format(percent, overAll * 100)
                progress_callback.emit(percent * 100, data)

            # close the newNode
            newNode.close()

            # add the img path to the list of built images
            images.append(nodeName)
        
        # update the image list 
        self.images2flash = images
        self.update_images_in_config(images)

        # close the file
        file.close()

    def detectCards(self):
        '''Detects and identify the uSD cards in the system OS agnostic'''

        # detected drives
        self.drives = []

        # OS specific listing
        aos = sys.platform.strip()
        if aos in ["win32", "cygwin"]:
            logging.debug("Detecting Windows Drives")
            self.drives = getWinDrivesInfo()
        elif aos.startswith('linux'):
            logging.debug("Detecting Linux Drives")
            self.drives = getLinDrivesInfo()
        else:
            logging.debug("Detecting MacOS Drives")
            self.drives = getMacDriveInfo()

        # build a user friendly string for the cards if there is a card
        if self.drives:
            driveList = []
            for (drive, label, size) in self.drives:
                # convert size from bytes to GB
                if int(size) > 0:
                    size = size / 2**30

                driveList.append("{} '{}' {:0.1f}GB".format(drive, label, size))
        else:
            driveList = ["Please insert a card"]

        self.cards = driveList

    @pyqtProperty(list, notify=cardsChanged)
    def cards(self):
        '''Return the cards list for the QML UI interface integration'''
        return self.cardList

    @cards.setter
    def cards(self, val):
        '''Setter of the card property for the combo box of the cards'''

        if self.cardList == val:
            return

        self.cardList = val[:]
        self.cardsChanged.emit()

    @pyqtSlot(str)
    def pickCard(self, text):
        '''Set the actual selected card in the combo box'''
        self.card = text.split(" ")[0]

    @pyqtProperty(list, notify=builtImagesChanged)
    def images2flash(self):
        '''Return the images list for the QML UI interface integration'''
        return self.builtImages

    @images2flash.setter
    def images2flash(self, val):
        '''Setter of the images property for the combo box of the cards'''

        if self.builtImages == val:
            return

        self.builtImages = val[:]
        self.builtImagesChanged.emit()

    @pyqtSlot(str)
    def pickimages2flash(self, text):
        '''Set the actual selected image in the combo box'''

        self.flashingNow = os.path.join(self.localPathBuild, text)
        print("You selected the image: {} to be flashed next".format(text))

    def dummy(self):
        '''Dummy function, return, some workers need this to work'''
        return

    @pyqtSlot()
    def imageFlash(self):
        '''Flash the images, one at a time, each one on a turn'''

        # failsafe if we are already on a flashing process
        if self.flashingOnProgress:
            logging.debug("User pressed the Flashing button during a flash, aborting")
            self.uiWarning.emit("Ops!", "Please wait until the actual flashing process ends.")
            return

        # stop the timer, it must not mess with the device on the copy process
        self.timerStop()

        # Preparing the flasher thread
        self.flash = Worker(self.flasher)
        self.flash.signals.data.connect(self.dummy)
        self.flash.signals.progress.connect(self.flashProg)
        self.flash.signals.result.connect(self.flashResult)
        self.flash.signals.error.connect(self.flashError)
        self.flash.signals.finished.connect(self.flashDone)

        #  start flashing thread
        self.threadpool.start(self.flash)
        self.flashingOnProgress = True

    def flasher(self, data_callback, progress_callback):
        '''Flash the images
        The actual image to flash is on self.flashingNow [image, name]'''

        if sys.platform in ["win32", "cygwin"]:
            # windows
            self.windowsFlasher(data_callback, progress_callback)
        elif sys.platform == "darwin":
            # mac
            self.macosFlasher(data_callback, progress_callback)
        else:
            # linux
            self.linuxFlasher(data_callback, progress_callback)

    def windowsFlasher(self, data_callback, progress_callback):
        '''Windows flasher'''

        # there are images left to burn, pick the first one
        image = self.flashingNow
        name = image.split(os.sep)[-1].split(".")[0]
        drive = self.card
        logfile = os.path.join(tempfile.gettempdir(), "skfpl.log")
        flasher = "flash.exe"
        size = os.path.getsize(image)

        # touch (& truncate) the logfile
        f = open(logfile, 'wt')
        f.write("0.0%\n")
        f.close()

        # user advice.
        data_callback.emit("Flashing now {} image".format(name))

        # remove the trailing \ on the drive name
        if "\\" in drive:
            drive = drive[:-1]

        # build the command to flash it
        cmd = "{} \"{}\" \"{}\" \"{}\"".format(flasher, image, drive, logfile)

        # logging
        logging.debug("Full cmd line is:\n{}".format(cmd))

        try:
            p = subprocess.Popen(cmd)
            flash_start = time.time()

            #  open the log file
            lf = open(logfile, 'rt')

            while p.poll() is None:
                #  capturing progress via a file
                l = lf.readline().strip("\n")
                if len(l) != 0:
                    # get time
                    now_time = time.time()

                    # check for errors
                    if l.startswith("ERROR"):
                        print("Error detected:\n{}".format(l))
                        return False

                    if "%" in l:
                        # we are on:
                        pr = float(l.strip()[:-1])
                        if pr > 0:
                            (speed, eta) = calc_speed_eta(size, pr, flash_start, now_time)
                            progress_callback.emit(pr, "Flashing {}: {}%, {}, {} left".format(name, pr, speed, eta))

            #  close the log file
            if lf:
                lf.close()

            # logging
            logging.debug("Return Code was {}".format(p.returncode))

            # check for return code
            if p.returncode == 0:
                # All ok, pop the image from the list
                return "Done"
            else:
                # different code
                # TODO capture an error
                return "Oops!"

        except OSError as e:
            logging.debug("Failed to execute program '%s': %s" % (cmd, str(e)))
            raise

        return "Done"

    def linuxFlasher(self, data_callback, progress_callback):
        '''Linux flasher'''

        #  command to run
        pkexec = getLinuxPath("pkexec")
        dd = getLinuxPath("dd")
        python = getLinuxPath("python3")
        logfile = os.path.join(tempfile.gettempdir(), "skf.log")

        # touch the logfile
        f = open(logfile, mode='wt')
        f.write("0.0%")
        f.close()

        # detect the streamer syntax
        if self.bundle:
            # I'm in a static pre compiled env
            streamer = os.path.join(self.appFolder, "pypv")
        else:
            # just a python call to the code
            streamer = python + " " + os.path.join(self.appFolder, "../posix-build/pypv.py")

        # there are images left to burn, pick the first one
        image = self.flashingNow
        name = image.split(os.sep)[-1].split(".")[0]
        destination = self.card
        size = os.path.getsize(image)

        data_callback.emit("Flashing now {} image".format(name))

        if pkexec and dd and (python or streamer):
            cmd = "{} {} {} | {} {} of={}".format(streamer, image, logfile, pkexec, dd, destination)
            logging.debug("Full cmd line is:\n{}".format(cmd))

            # TODO Test if the destination file is in there

            try:
                p = subprocess.Popen(cmd, shell=True)
                flash_start = time.time()

                #  open the log file
                lf = open(logfile, 'r')

                while p.poll() is None:
                    #  capturing progress via a file
                    l = lf.readline().strip("\n")
                    if len(l) != 0:
                        # get time
                        now_time = time.time()

                        # check for errors
                        if l.startswith("ERROR"):
                            print("Error detected:\n{}".format(l))
                            return False

                        if "%" in l:
                            pr = float(l.strip()[:-1])

                            if pr > 0:
                                (speed, eta) = calc_speed_eta(size, pr, flash_start, now_time)
                                progress_callback.emit(pr, "Flashing {}: {}%, {}, {} left".format(name, pr, speed, eta))

                #  close the log file
                if lf:
                    lf.close()

                logging.debug("Return Code was {}".format(p.returncode))

                # check for return code
                if p.returncode == 0:
                    # All ok, pop the image from the list
                    return "Done"
                else:
                    # different code
                    # TODO capture an error
                    return "Oops!"

            except OSError as e:
                logging.debug("Failed to execute program '%s': %s" % (cmd, str(e)))
                raise
        else:
            logging.debug("Error getting one of the dependencies")

            # user warning
            self.uiWarning.emit("Ops!", "There was an utility missing in your system!")

    def macosFlasher(self, data_callback, progress_callback):
        '''Macos flasher'''

        #  command to run
        dd = getLinuxPath("dd")
        python = getLinuxPath("python3")
        logfile = os.path.join(tempfile.gettempdir(), "skf.log")

        # touch the logfile
        f = open(logfile, mode='wt')
        f.write("0.0%")
        f.close()

        # detect the streamer syntax
        if self.bundle:
            # I'm in a static pre compiled env
            streamer = os.path.join(self.appFolder, "pypv")
        else:
            # just a python call to the code
            streamer = python + " " + os.path.join(self.appFolder, "../posix-build/pypv.py")

        print("Streamer tool is at: {}".format(streamer))

        # there are images left to burn, pick the first one
        image = self.flashingNow
        name = image.split(os.sep)[-1].split(".")[0]
        destination = self.card
        size = os.path.getsize(image)

        data_callback.emit("Flashing now {} image".format(name))

        # umount the drive
        getDataFromCLI("diskutil unmountDisk {}".format(destination))

        if dd and (python or streamer):
            cmd = "{} {} {} | {} of={}".format(streamer, image, logfile, dd, destination)
            logging.debug("Basic cmd line is:\n{}".format(cmd))

            # pack the cmd in the long sentence to ask for permissions
            realcmd = "osascript -e 'do shell script \"{}\" with administrator privileges'".format(cmd)
            print("Full command is like this:\n")
            print(realcmd)

            try:
                p = subprocess.Popen(realcmd, shell=True)
                flash_start = time.time()

                #  open the log file
                lf = open(logfile, 'r')

                while p.poll() is None:
                    #  capturing progress via a file
                    l = lf.readline().strip("\n")
                    if len(l) != 0:
                        # get time
                        now_time = time.time()

                        # check for errors
                        if l.startswith("ERROR"):
                            print("Error detected:\n{}".format(l))
                            return False

                        if "%" in l:
                            # we are on:
                            pr = float(l.strip()[:-1])
                            if pr > 0:
                                (speed, eta) = calc_speed_eta(size, pr, flash_start, now_time)
                                progress_callback.emit(pr, "Flashing {}: {}%, {}, {} left".format(name, pr, speed, eta))

                #  close the log file
                if lf:
                    lf.close()

                logging.debug("Return Code was {}".format(p.returncode))

                # check for return code
                if p.returncode == 0:
                    # All ok, pop the image from the list
                    return "Done"
                else:
                    # different code
                    # TODO capture an error
                    return "Oops!"

            except OSError as e:
                logging.debug("Failed to execute program '%s': %s" % (cmd, str(e)))
                raise
        else:
            logging.debug("Error getting one of the dependencies")

            # user warning
            self.uiWarning.emit("Ops!", "There was an utility missing in your system!")

    def loadPrevious(self):
        '''WARNING legacy procedure, will be removed in future versions, deprecated in favor of
        the use of configparser and a config file; now returns the file and version as a tuple
        or a (false, false)

        Original docstring follows

        Check for a already downloaded and checksum tested image in the
        downloads folder

        If so enable the next steps, and show a comment to the user, the fact
        that we have an already downloaded and validated image is shown buy
        the precense of a file called '.checked' with the name of the file in
        the downlads folder.
        '''

        # DEBUG
        logging.debug("===> Starting to load previous work")

        #  check if a file named .checked is on the downloads path
        baseImage = ""
        checked = os.path.join(self.localPathDownloads, '.checked')
        if os.path.exists(checked):
            # DEBUG
            logging.debug("Checked File exist")

            f = open(checked)
            baseImage = f.readline().strip("\n")
            f.close()
            baseImageFile = baseImage.split(os.path.sep)[-1]

            # DEBUG
            logging.debug("Base image from checked file is {}".format(baseImage))

        else:
            # DEBUG
            logging.debug("No checked file found")

        if baseImage != "":
            # DEBUG
            logging.debug("Base image is set in checked file")

            if os.path.exists(baseImage):
                # DEBUG
                logging.debug("Base image exist on file system")
                logging.debug("Loading....{}".format(baseImageFile))

                return (baseImage, self.getSkybianVersion(baseImage))

                # DEBUG
                logging.debug("Base image version is {}".format(self.skybianFileVersion))
            else:
                # DEBUG
                logging.debug("Base image does not exist")

                # check file exist but image don't, erasing it
                os.unlink(checked)

                # DEBUG
                logging.debug("Checked file erased as it's not useful")
        else:
            # DEBUG
            logging.debug("Base image from checked is empty")

            if os.path.exists(checked):
                os.unlink(checked)

                # DEBUG
                logging.debug("Checked file erased as it's not useful")

        # if you get here is tha there is no file
        return (False, False)

    def checkForUpdates(self):
        '''Check for updates in a thread to not disturb the UI flow'''

        logging.debug("===> Starting to check for updates")

        # Preparing the check update thread
        self.ckup = Worker(checkUpdates)
        self.ckup.signals.data.connect(self.dummy)
        self.ckup.signals.progress.connect(self.dummy)
        self.ckup.signals.result.connect(self.checkUpdatesResult)
        self.ckup.signals.error.connect(self.dummy)
        self.ckup.signals.finished.connect(self.dummy)

        #  start flashing thread
        self.threadpool.start(self.ckup)

    def updateSkybianURL(self):
        '''Fetch the information about the lastest testnet/mainnet version
        of Skybian from the internet
        '''

        # Preparing the check update thread
        self.updl = Worker(getLatestSkybian)
        self.updl.signals.data.connect(self.dummy)
        self.updl.signals.progress.connect(self.dummy)
        self.updl.signals.result.connect(self.skybianUrlResult)
        self.updl.signals.error.connect(self.dummy)
        self.updl.signals.finished.connect(self.dummy)

        #  start flashing thread
        self.threadpool.start(self.updl)

    @pyqtSlot(bool)
    def defaultNetwork(self, status):
        '''Receives a signal with the value of the default network check box'''

        # which value
        if status:
            # ticked: default values
            conf = self.create_config(True)
            self.config['NET'] = conf['NET']
            self.save_config()

    def get_config(self):
        '''Get the config file and load it. If empty or not present then create it with a basic structure.

        This process triggers the status of the App in the following order:

        MAIN > setup = yes|no (if no)
            Abort config, just created a new one

        SKYBIAN > verified = yes|no (if yes)
            Process and load the skybian file (check if there, etc)
            Triggers the network part show

        NET > default = yes|no (if no)
            Load net parameters as local vars
            Validate the local net config
            upload it to the UI

        IMAGES > generated = yes|no (if yes)
            load the values
            Check if the files are there
            Load them in the class var
            Update the UI.

        '''

        #### Internal procedures follows

        # reset skybian config
        def reset_skybian_config():
            '''To reset the SKYBIAN section fo the config to the default values'''

            # get the default config
            conf = self.create_config(True)
            self.config['SKYBIAN'] = conf['SKYBIAN']
            self.save_config()

        # if the net config stored the default one?
        def is_net_conf_default():
            '''Returns true or false if the net config is the same as the default'''

            # get the default config
            conf = self.create_config(True)
            if self.config['NET'] == conf['NET']:
                return True
            else:
                return False

        # reset net config
        def reset_net_config():
            '''To reset the NET section of the config to the default values'''

            # get the default config
            conf = self.create_config(True)
            self.config['NET'] = conf['NET']
            self.save_config()

        # is there?
        if not os.path.exists(self.config_file):
            # create a new one
            logging.debug("Config File not present, creating one")
            self.create_config()

        # fail safe for invalid data
        try:
            # now load it
            self.config.read(self.config_file)
            logging.debug("Config File loaded, parsing...")

            # validate some of the config items
            if self.config['MAIN']['setup'] == 'no':
                # first run, don't load anything
                logging.debug("First time run, default loaded")

                # resetting it to protect us from a sloppy/curious user
                self.create_config()
            else:
                # non default config
                logging.debug("Config file has custom data")

            # TODO
            # DEPRECATED erase this 'if' on ver 0.7 and forward
            if self.config['SKYBIAN']['verified'] == 'no':
                logging.debug("Skybian file not verified acording to config file, testing the filesystem...")

                # try to detect it on the fs
                (file, version) = self.loadPrevious()

                if file != False:
                    logging.debug("Found a valid local skybian copy, loading it [WARNING! this feature will be deprecated]")
                    self.config['SKYBIAN'] = {
                                            'verified' : 'yes',
                                            'file' : file,
                                            'version' : version,
                                        }
                    self.save_config()

            # skybian present ?
            if self.config['SKYBIAN']['verified'] == 'yes':
                skybian_file = self.config['SKYBIAN']['file']
                if os.path.exists(skybian_file):
                    logging.debug("Skybian file already on the FS, so we will use it")
                    self.skybianFile = skybian_file
                    self.skybianFileVersion = self.config['SKYBIAN']['version']

                    self.extractionOK = True
                    self.setStatus.emit("Using local file: {}".format(shortenPath(self.skybianFile, -1)))
                    self.dData.emit("Open the <a href='file://{}'>work image folder</a>".format(self.localPathBuild))
                    self.netConfig.emit()
                    self.buildImages.emit()

                else:
                    # Verified but the file is not present... ?
                    logging.debug("Config file says there is a skybian image, but we can't find it... fixing config")
                    reset_skybian_config()

            else:
                # reset config
                reset_skybian_config()
                logging.debug("No custom config about the Skybian file")

            # Test the net part
            if self.config['NET']['configured'] == 'yes':
                # net part appears to be in place
                logging.debug("NET section custom config detected.")

                # is net conf default?
                if not is_net_conf_default():
                    logging.debug("NET section config is loaded and not the default, validating...")
                    # load the net parameters as locals and validate them before passing to the app
                    lgw = self.config['NET']['gw']
                    ldns = self.config['NET']['dns']
                    lmanager = self.config['NET']['manager']
                    lcount = self.config['NET']['count']

                    # now test them
                    result = self.validateNetworkData(lgw, ldns, lmanager, lcount, ui=False)
                    if result:
                        # ok, network data in place
                        logging.debug("NET section config validated...")

                        # tell the UI that we need the Network visible
                        self.netDefaultBox.emit(False)

                    else:
                        # Failed to validate
                        logging.debug("NET section config is broken, resetting to defaults...")

                        # Load defaults and notify UI
                        self.netDefaultBox.emit(True)
                        reset_net_config()

                else:
                    # logging
                    logging.debug("NET section config is default, loading...")

                    # reset it just in case
                    self.netDefaultBox.emit(True)
                    reset_net_config()

            else:
                logging.debug("No custom config about the network parameters")

            # Test the images part
            if self.config['IMAGES']['generated'] == 'yes':
                # ok, we have a set of images generated
                logging.debug("IMAGES section has some generated images, parsing it...")

                # this var will hold the image list from the config & FS
                images = []

                for (option, value) in self.config['IMAGES'].items():
                    # filter just the image ones
                    if 'image' in option:
                        if value is '':
                            continue

                        if os.path.isfile(value):
                            # is there, adding it to the count
                            images.append(value)
                            logging.debug("Adding image: {}".format(value))
                        else:
                            # not there but in file, pop the config
                            self.config.remove_option('IMAGES', option)
                            self.save_config()
                            logging.debug("Config image {} not found, removing from config".format(value))

                # images has the valid images from the config and FS, passing it to main class
                self.images2flash = [x[x.rfind(os.path.sep) + 1:] for x in images]

                # notify the UI about the images
                self.bFinished.emit()

                # check for cards timer start
                self.timerStart()
            else:
                logging.debug("No custom config about the local generated images")
        except:
            # some error in the loading of the config with bad parameters or simply the user
            # mangled it trying to fix/force something.

            # create a new clean config
            self.create_config()

            # now load it
            self.config.read(self.config_file)
            logging.debug("Mangled config file detected, resetting it and loading defaults")

            # erase old/previous (now orphaned) images from the default dir
            logging.debug("As we are resetting we need to also erase the now orphaned images on this system")
            flist = os.listdir(self.localPathBuild)
            for f in flist:
                if ".img" in f:
                    item = os.path.join(self.localPathBuild, f)
                    if os.path.isfile(item):
                        os.unlink(item)
                        logging.debug("Orphaned file {} erased".format(item))

    def create_config(self, passit = False):
        '''Create a empty and default config file in the local filesystem'''

        conf = configparser.ConfigParser()
        conf['MAIN'] = {
                            'setup' : 'no',
                            }

        conf['SKYBIAN'] = {
                            'verified' : 'no',
                            'file' : '',
                            'version' : '',
                            }

        conf['NET'] = {
                            'configured' : 'no',
                            'gw' : '192.168.0.1',
                            'dns' : '1.0.0.1, 1.1.1.1',
                            'manager' : '192.168.0.2',
                            'count' : '2',
                            }

        conf['IMAGES'] = {
                            'generated' : 'no',
                            'image0' : ''
                            }

        if passit is False:
            self.config = conf
            self.save_config()
        else:
            return conf

    def save_config(self):
        '''Save the configuration in the filesystem'''

        with open(self.config_file, 'wt') as configfile:
            ret = self.config.write(configfile)
            logging.debug("Configuration Saved/Updated")


    def update_images_in_config(self, images):
        '''Get the list of images built and update the config file with them'''

        # no parameters passed
        if len(images) is 0:
            return

        # ok, it's time to update.
        self.config['IMAGES']['generated'] = 'yes'
        logging.debug("IMAGES section needs update")

        # images...
        for i in range(len(images)):
            self.config['IMAGES']['image{}'.format(i)] = os.path.join(self.localPathBuild, images[i])

        # save config file.
        self.save_config()

# load the instance
Skyflash.instance = Skyflash()
