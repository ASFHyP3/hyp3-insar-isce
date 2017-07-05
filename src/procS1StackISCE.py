#!/usr/bin/env python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
###############################################################################
# procS1StackISCE.py 
#
# Project:   
# Purpose:  Wrapper script for processing a stack of Sentinel-1 with ISCE
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
import sys
import os
from lxml import etree
import re
import getSubSwath
from shutil import copyfile
from shutil import move
from iscegeo2geotif import convert_files
import get_dem
from osgeo import gdal
import dem2isce
from execute import execute
import argparse
import file_subroutines
from procS1ISCE import procS1ISCE
import saa_func_lib as saa

    
#####################
#
# Define procedures
#
#####################

def isceProcess(bname,ss,step):
    cmd = 'cd %s/%s ; ' % (bname,ss)
    cmd = cmd + 'topsApp.py %s' % step
    execute(cmd)

def makeDirAndXML(date1,date2,file1,file2,demFlag,options):
    dirname = '%s_%s' % (date1,date2)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    roi = []
    roi.append(options['south'])
    roi.append(options['north'])
    roi.append(options['west'])
    roi.append(options['east'])
    
    if demFlag:
        procS1ISCE(options['swath'],file1,file2,gbb=roi,xmlFlag=True,unwrapFlag=True,demFile=options['demname'])
    else:
        procS1ISCE(options['swath'],file1,file2,gbb=roi,xmlFlag=True,unwrapFlag=True)

def getImageFiles(mydir,ss):
    os.chdir("%s/%s/merged" % (mydir,ss))
    convert_files()
    copyfile("colorized.jpg","../../../PRODUCT/%s_%s.jpg" % (mydir,ss))
    copyfile("phase.tif","../../../PRODUCT/%s_%s.phase.tif" % (mydir,ss))
    copyfile("amp.tif","../../../PRODUCT/%s_%s.amp.tif" % (mydir,ss))
    copyfile("coherence.tif","../../../PRODUCT/%s_%s.coh.tif" % (mydir,ss))
    os.chdir("../../../")
    
def makeMetadataFile(basedir,ss):
   # Get the platform heading
    for mydir in os.listdir("."):
        if ".SAFE" in mydir and os.path.isdir(mydir):
            os.chdir("%s/annotation" % mydir)
            for myfile in os.listdir("."):
                if "001.xml" in myfile:
                    root = etree.parse(myfile)
                    for head in root.iter('platformHeading'):
                        heading = float(head.text)              
          	        print "Found heading %s" % heading
                        break
                    else:
                        continue
                    break
            else:
                continue
            break
    os.chdir("../..")

    # Get the UTC time and Bperp
    os.chdir("%s/%s" % (basedir,ss))
    g = open('isce.log','r')
    for line in g.readlines():
        if "subset.Overlap 0 start time" in line:
            t = re.split('=',line)
            utctime=t[1]
            print "Found utctime %s" % utctime
        if "Bperp at midrange for first common burst" in line:
            t = re.split('=',line)
            baseline=t[1]
            print "Found baseline %s" % baseline
    os.chdir("../..")
    t = re.split(' ',utctime)
    s = re.split(":",t[2])
    utctime = ((int(s[0])*60+int(s[1]))*60)+float(s[2])

    f = open('PRODUCT/%s_%s.txt' % (basedir,ss),'w')
    f.write("baseline: %s" % baseline)
    f.write("utctime: %s\n" % utctime)
    f.write("heading: %s" % heading)

##########################################################################
# Main Entry Point
#
#        csvFile = input file to read granules from and use get_asf.py
#        demFlag = If true, use get_dem instead of opentopo
#        roi     = Region of interest, defined as (south north west east)
#        ss      = Subswath to process
# 
#        roi and ss are mutually exclusive required parameters. 
#
##########################################################################
def procS1StackISCE(csvFile=None,demFlag=False,roi=None,ss=None):

    if (roi is None and ss is None):
        print "ERROR: must specifiy one of ROI or SS"
        sys.exit(1)
    if (roi is not None and ss is not None):
        print "ERROR: can only specify one of ROI or SS"
	sys.exit(1)
	
    options = {}

    if ss is not None:
        options['swath'] = int(ss)

    # If file list is given, download the files
    if csvFile is not None:
        file_subroutines.prepare_files(csvFile)

    (filenames,filedates) = file_subroutines.get_file_list()

    print filenames
    print filedates

    # If no ROI is given, determine one from first file
    if roi is None:
        mydir = "%s/annotation" %  filenames[0]
        myxml = ""
        name = ""
        if options['swath']==1:
            name = "001.xml"
        elif options['swath']==2:
            name = "002.xml"
        elif options['swath']==3:
            name = "003.xml"
        else:
            print "Invalid sub-swath specified %s" % options['swath']

        for myfile in os.listdir(mydir):
            if name in myfile:      
                myxml = "%s/annotation/%s" % (filenames[0],myfile)
        print "Found annotation file %s" % myxml
    
        lat_max,lat_min,lon_max,lon_min = getSubSwath.get_bounding_box(myxml)
    
        options['south']=lat_min
        options['north']=lat_max
        options['west']=lon_min
        options['east']=lon_max
    else:
        options['south'] = roi[0]
        options['north'] = roi[1]
        options['west'] = roi[2]
        options['east'] = roi[3]

        # We were given a ROI, calculate the subswath
        options['swath'], roi = getSubSwath.SelectSubswath(filenames[0],options['west'],options['south'],options['east'],options['north'])
        if options['swath'] == 0:
            sys.exit("ERROR: No overlap of bounding box with imagery")
        print "Found subswath %s to process" % options['swath']
    
        options['south']=roi[0]
        options['north']=roi[1]
        options['west']=roi[2]
        options['east']=roi[3]

    if demFlag:
        get_dem.get_dem(options['west'],options['south'],options['east'],options['north'],"stack_dem.tif",False)

	# If DEM is from NED13, then it will have a NAD83 ellipse - need to convert to WGS84
	(x1,y1,t1,p1) = saa.read_gdal_file_geo(saa.open_gdal_file("stack_dem.tif"))
	if "NAD83" in p1:
	    gdal.Warp("stack_dem_wgs84.tif","stack_dem.tif", dstSRS="EPSG:4326")
	    move("stack_dem_wgs84.tif","stack_dem.tif")

        # Convert DEM file into ISCE format
        gdal.Translate("stack_dem.dem","stack_dem.tif",format="ENVI")
        dem2isce.dem2isce("stack_dem.dem","stack_dem.hdr","stack_dem.dem.xml")
        options['demname'] = "stack_dem.dem"

    length=len(filenames)

    # Make XML files for pairs and 2nd pairs
    for x in xrange(length-2):
        makeDirAndXML(filedates[x],filedates[x+1],filenames[x],filenames[x+1],demFlag,options)
        makeDirAndXML(filedates[x],filedates[x+2],filenames[x],filenames[x+2],demFlag,options)

    # If we have anything to process
    if (length > 1) :
        # Make XML files for last pair
        makeDirAndXML(filedates[length-2],filedates[length-1],filenames[length-2],filenames[length-1],demFlag,options)

        if not os.path.exists("PRODUCT"):
            os.mkdir("PRODUCT")

        # Run through directories processing ifgs and collecting results as we go
        for mydir in os.listdir("."):
            if len(mydir) == 17 and os.path.isdir(mydir) and "_20" in mydir:
                print "Processing directory %s" % mydir
                ss = 'iw'+str(options['swath'])
                isceProcess(mydir,ss," ")
	        if os.path.isdir("%s/%s/merged" % (mydir,ss)):
                    print "Collecting directory %s" % mydir
		    getImageFiles(mydir,ss)
		    makeMetadataFile(mydir,ss)

###########################################################################

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Create a stack of interferograms using ISCE software")
  parser.add_argument("-f","--file",help="Input CSV file of granules, otherwise process all SAFE files in the current directory")
  parser.add_argument("-d","--dem", action="store_true",help="Use get_dem to get the DEM file instead of opentopo")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-r","--roi",nargs=4,type=float,help="Set geocoding bounding box (south north west east), othwerwise calculate bounding box from first image")
  group.add_argument("-s","--ss",help="Set the subswath to process. If ROI is specified, calculate subswath")
  args = parser.parse_args()

  procS1StackISCE(csvFile=args.file,demFlag=args.dem,roi=args.roi,ss=args.ss)


