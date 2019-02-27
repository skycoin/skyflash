# part of skyflash

import os
import sys
from glob import glob

module_dir = os.path.dirname(sys.modules["skyflash"].__file__)
__all__ = []
for i in sorted(glob(os.path.join(module_dir, "*.py"))):
    name = os.path.basename(i)[:-3]
    if not name.startswith("__"):
        __all__.append(name)

# Version
name = "skyflash"

# GUI imports
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import QFileInfo

# local imports
from skyflash.skyflash import Skyflash
from skyflash.utils import *

def app():
    '''Run the app'''

    #  privilege elevation request in Windows.
    if sys.platform in ["win32", "cygwin"]:
        bootstrap()

    try:
        # GUI app
        app = QGuiApplication(sys.argv)
        appPath = QFileInfo(__file__).absolutePath()
        app.setWindowIcon(QIcon(os.path.join(appPath, 'skyflash.png')))

        # debug
        print("App path is: {}".format(appPath))

        # app instance
        skyflash = Skyflash()

        # main workspace, skyflash object
        path, download, checked = setPath("Skyflash")
        skyflash.localPath = path
        skyflash.localPathDownloads = download
        skyflash.checked = checked

        # init the logging.
        skyflash.logStart()

        # startting the UI engine
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("skf", skyflash)

        # Conditional QML file loading, first try to load it from the local folder
        localQML = os.path.join(appPath, "data" + os.sep + "skyflash.qml")
        if os.path.exists(localQML):
            # local qml file
            engine.load(localQML)
        else:
            # other locations by OS
            if sys.platform.startswith('linux'):
                # first locally, then on deb install path
                installedQML = "/usr/share/skyflash/skyflash.qml"
                if os.path.exists(installedQML):
                    # the one installed by the .deb package
                    engine.load(installedQML)
                else:
                    # cant find the QML file
                    print("Crap! I'm unable to find a file I need to render the user interface, exiting")
                    sys.exit(-1)
            else:
                    # cant find the QML file
                    print("Crap! I'm unable to find a file I need to render the user interface, exiting")
                    sys.exit(-1)

        # connect the engine
        engine.quit.connect(app.quit)

        # check to see if we can load a previous downloaded & tested image
        skyflash.loadPrevious()

        # main GUI call
        sys.exit(app.exec_())
    except SystemExit:
        sys.exit("By, see you soon.")
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
        sys.exit(-1)