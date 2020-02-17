#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
###############################################################################
# procAllS1StackISCE.py 
#
# Project:   
# Purpose:  Script for processing all swaths of a stack of Sentinel-1 with ISCE
#          
# Author:   Tom Logan
#
###############################################################################
# Copyright (c) 2017, Alaska Satellite Facility
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
# 
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
###############################################################################

#####################
#
# Import all needed modules right away
#
#####################
from __future__ import print_function

import sys
import getSubSwath
import argparse
from procS1StackISCE import procS1StackISCE
from file_subroutines import prepare_files
from file_subroutines import get_file_list

###########################################################################
# Main Entry Point:
#
#        south,north,west,east -- bounding box
#        csvFile = file to fetch granules from using get_asf.py
#        demFlag = if TRUE, use ASF get_dem instead of opentopo
#
###########################################################################
def procAllS1StackISCE(south,north,west,east,csvFile=None,demFlag=None):

    # If file list is given, download the files and unzip them
    if csvFile is not None:
        prepare_files(csvFile)

    (filenames,filesdates) = get_file_list()
        
    swaths,roi = getSubSwath.SelectAllSubswaths(filenames[0],west,south,east,north)

    if len(swaths) == 0:
        sys.exit("ERROR: No overlap of bounding box with imagery")
    print("Found %s subswath(s) to process" % len(swaths))

    for subswath in swaths:
        procS1StackISCE(demFlag=demFlag,ss=int(subswath))
    

###########################################################################

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Create All interferograms overlapping the ROI using ISCE")
  parser.add_argument("south",help="Minimum latitude")
  parser.add_argument("north",help="Maximum latitude")
  parser.add_argument("west",help="Minimum longitude")
  parser.add_argument("east",help="Maximm longitude")
  parser.add_argument("-f", "--file", help="list of files to download, in csv format")
  parser.add_argument("-d", "--dem", action="store_true", help="Use the ASF DEM heap instead of opentopo")
  args = parser.parse_args()

  procAllS1StackISCE(args.south,args.north,args.west,args.east,csvFile=args.file,demFlag=args.dem)
