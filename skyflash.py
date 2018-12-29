#!/usr/bin/env python3

# basic libs
import sys
import os
import traceback

try:
    input = raw_input
except:
    pass

# QT5 imports
try:
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
except ImportError as error:
    print('Import error: {}'.format(error))
    input('\nError importing libraries\nPress [Return] to exit')
    exit(1)

# main app
class ApplicationWindow(QMainWindow):

    # initializer function
    # Basically draw the interface and init the vars
    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("Skyflash")

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit, Qt.CTRL + Qt.Key_Q)

        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        self.main_widget = QWidget(self)

        #### main layout
        mainLayout = QVBoxLayout(self.main_widget)

        #### image widget definition
        image_widget = QVBoxLayout()

        # adding widgets to the layout 
        limage = QLabel("1. Skybian base image source")
        image_widget.addWidget(limage)

        # adding the horizontal layout for the buttons
        image_buttons = QHBoxLayout()

        # push buttons % label
        bdownload = QPushButton(text="Download Skybian", width=16)
        blocal = QPushButton(text="Browse local",  width=16)
        limagebuttons = QLabel("Select a local image or download one")
        
        # add elements to image button widgets
        image_buttons.addWidget(bdownload)
        image_buttons.addWidget(blocal)
        image_buttons.addWidget(limagebuttons)
        
        # add widget to image widget
        image_widget.addLayout(image_buttons) 

        # add it to main widget
        mainLayout.addLayout(image_widget)

        #### net widget definition
        net_widget = QVBoxLayout()

        # network label
        lnet = QLabel("2. Network settings")
        net_widget.addWidget(lnet)

        # check box 
        self.cskyminer_default = QCheckBox("Use skyminers default (1 manager and 7 nodes)")
        self.cskyminer_default.setChecked(True)
        net_widget.addWidget(self.cskyminer_default)

        # gateway & manager layout
        image_gateway = QHBoxLayout()
        image_manager = QHBoxLayout()

        # element def
        lgateway = QLabel("Gateway:")
        self.tgateway = QLineEdit("192.168.0.1", width=16)
        ldns = QLabel("DNS:")
        self.tdns = QLineEdit("1.0.0.1, 1.1.1.1", width=30)

        # add them
        image_gateway.addWidget(lgateway)
        image_gateway.addWidget(self.tgateway)
        image_gateway.addWidget(ldns)
        image_gateway.addWidget(self.tdns)

        # add layout to net
        net_widget.addLayout(image_gateway)

        # elements
        lmanager = QLabel("Manager IP:")
        self.tmanager = QLineEdit("192.168.0.1", width=16)
        lnodescount = QLabel("Nodes to generate:")
        self.tnodescount = QLineEdit("7", width=4)

        # add them
        image_manager.addWidget(lmanager)
        image_manager.addWidget(self.tmanager)
        image_manager.addWidget(lnodescount)
        image_manager.addWidget(self.tnodescount)
        image_manager.addStretch()

        # add layout to net
        net_widget.addLayout(image_manager)

        # add it to main widget
        mainLayout.addLayout(net_widget)

        #### build widget definition
        build_widget = QVBoxLayout()

        # build label
        lbuild = QLabel("3. Build images")
        build_widget.addWidget(lbuild)

        # layout for build button and progress bar
        build_build_widget = QHBoxLayout()

        # build button
        bbuild = QPushButton(text="Build Images", width=16)
        build_build_widget.addWidget(bbuild)

        # progress bar
        self.buildbar = QProgressBar()
        self.buildbar.isTextVisible = True
        self.buildbar.setMaximum(100)
        self.buildbar.setMinimum(0)
        self.buildbar.setValue(0)
        build_build_widget.addWidget(self.buildbar)

        # add build build layout to the build layout
        build_widget.addLayout(build_build_widget)

        # add it to main widget
        mainLayout.addLayout(build_widget)

        #### flash widget definition
        flash_widget = QVBoxLayout()

        lflash = QLabel("4. Flash the uSD cards, select the card & press the button")
        flash_widget.addWidget(lflash)

        # layout for combo + button
        flash_flash_widget = QHBoxLayout()

        # combo box, the updates will be timed on data change
        # TODO auto update of the mmcblk devices
        self.cbusd = QComboBox()
        flash_flash_widget.addWidget(self.cbusd)

        # flash button
        self.bflash = QPushButton(text="Flash all uSD cards")
        flash_flash_widget.addWidget(self.bflash)

        # add layout to parent
        flash_widget.addLayout(flash_flash_widget)

        # flash this card progress bar
        self.flashsdbar = QProgressBar()
        self.flashsdbar.isTextVisible = True
        self.flashsdbar.setMaximum(100)
        self.flashsdbar.setMinimum(0)
        self.flashsdbar.setValue(0)
        flash_widget.addWidget(self.flashsdbar)

        # flash ll cards progress bar
        self.flashallbar = QProgressBar()
        self.flashallbar.isTextVisible = True
        self.flashallbar.setMaximum(100)
        self.flashallbar.setMinimum(0)
        self.flashallbar.setValue(0)
        flash_widget.addWidget(self.flashallbar)

        # add it to the main layout
        mainLayout.addLayout(flash_widget)

        # Status bar
        self.status = self.statusBar()
        self.status.showMessage("Ready")

        # focus on the main widget
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    # quit the gui
    def fileQuit(self):
        self.close()

    # about box
    def about(self):
        QMessageBox.about(self, "About", \
"""Skyflash tools

A tool to configure and flash skybian default
image to uSD cards for the official skyminer
hardware of the Skycoin project.

Skycoin: http://github.com/skycoin/skycoin
Skybian: http://github.com/simelo/skybian
Skyflash: http://github.com/simelo/skyflash

""")

app = QApplication(sys.argv)
app.setOrganizationName("CO7WT Soft")
app.setOrganizationDomain("co7wt.blogger.com")
app.setApplicationName("Intrument PC interface")

aw = ApplicationWindow()
# aw.setWindowTitle("%s" % "Intrument PC interface")
aw.show()
sys.exit(app.exec_())
