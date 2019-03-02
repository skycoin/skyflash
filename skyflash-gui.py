#!/usr/bin/env python3

import os

runPath = os.getcwd()
print("Run Path is: {}".format(runPath))

import skyflash
skyflash.runPath = runPath
skyflash.app()

