#!/usr/bin/env python3

import sys
import os
import argparse

# parsing the input args
parser = argparse.ArgumentParser()
parser.add_argument("inputfile", help="The file to stream to dd to flash it")
parser.add_argument("logfile", help="The file to log the activity")
args = parser.parse_args()

# args parse
try:
    # parse args ans do a initial check up
    inputfile = args.inputfile
    size = os.path.getsize(inputfile)
    stream = open(inputfile, mode='rb', buffering=1)
    logfile = args.logfile
    log = open(logfile, mode='wt', buffering=1)
except:
    sys.stderr.write("There was an error parsing the command line parameters,\nplease run the command with the -h switch to know more.\n\n")
    sys.stderr.write("{}\n".format(sys.exc_info()[1]))
    sys.exit()

# percent tracking vars
writed = 0
apc = 0
chunk = 512*100

# Main loop
while True:
    # get the data in the stdin buffer
    buffer = stream.read(chunk)

    # check if there is still data to be passed
    if len(buffer) > 0:
        # write
        sys.stdout.buffer.write(buffer)
        writed += len(buffer)

        # calc percent & update lf
        cpc = int(1000 * writed / size)
        if cpc > apc:
            apc = cpc
            log.write("{:.1%}\n".format(apc/1000))
    else:
        # no more data exit
        break

# close the file handlers
log.close()
stream.close()
sys.exit()
