#!/usr/bin/env python
"""Script for processing all swaths of a stack of Sentinel-1 with ISCE"""

from __future__ import print_function

import argparse
import sys

from hyp3lib import getSubSwath
from hyp3lib.file_subroutines import get_file_list
from hyp3lib.file_subroutines import prepare_files

from hyp3insarisce.procS1StackISCE import procS1StackISCE


def procAllS1StackISCE(south, north, west, east, csvFile=None, demFlag=None):
    """Main Entry Point:

        south,north,west,east -- bounding box
        csvFile = file to fetch granules from using get_asf.py
        demFlag = if TRUE, use ASF get_dem instead of opentopo
    """
    # If file list is given, download the files and unzip them
    if csvFile is not None:
        prepare_files(csvFile)

    (filenames, filesdates) = get_file_list()

    swaths, roi = getSubSwath.SelectAllSubswaths(filenames[0], west, south, east, north)

    if len(swaths) == 0:
        sys.exit("ERROR: No overlap of bounding box with imagery")
    print("Found {} subswath(s) to process".format(len(swaths)))

    for subswath in swaths:
        procS1StackISCE(demFlag=demFlag, ss=int(subswath))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create All interferograms overlapping the ROI using ISCE")
    parser.add_argument("south", help="Minimum latitude")
    parser.add_argument("north", help="Maximum latitude")
    parser.add_argument("west", help="Minimum longitude")
    parser.add_argument("east", help="Maximm longitude")
    parser.add_argument("-f", "--file", help="list of files to download, in csv format")
    parser.add_argument("-d", "--dem", action="store_true", help="Use the ASF DEM heap instead of opentopo")
    args = parser.parse_args()

    procAllS1StackISCE(args.south, args.north, args.west, args.east, csvFile=args.file, demFlag=args.dem)
