#!/usr/bin/env python
"""Create a stack of interferograms using ISCE software"""

from __future__ import print_function

import argparse
import os
import re
import sys
from shutil import copyfile

from hyp3lib import file_subroutines, getSubSwath, __version__
from hyp3lib import saa_func_lib as saa
from hyp3lib.execute import execute
from hyp3lib.get_dem import get_ISCE_dem
from hyp3lib.iscegeo2geotif import convert_files
from lxml import etree
from six.moves import range

from hyp3insarisce.proc_s1_isce import proc_s1_isce


def isce_process(bname, ss, step):
    cmd = 'cd {bname}/{ss} ; topsApp.py {step}'.format(bname=bname, ss=ss, step=step)
    execute(cmd)


def make_dir_and_xml(date1, date2, file1, file2, dem, options):
    dirname = '{date1}_{date2}'.format(date1=date1, date2=date2)
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    roi = [options['south'], options['north'], options['west'], options['east']]

    if dem:
        proc_s1_isce(options['swath'], file1, file2, gbb=roi, xml=True, unwrap=True, dem=options['demname'])
    else:
        proc_s1_isce(options['swath'], file1, file2, gbb=roi, xml=True, unwrap=True)


def get_image_files(mydir, ss, options):
    os.chdir("%s/%s/merged" % (mydir, ss))
    proj = saa.get_utm_proj(options['west'], options['east'], options['south'], options['north'])
    convert_files(True, proj=proj, res=30)
    copyfile("colorized_unw.png", "../../../PRODUCT/%s_%s_unw_phase.png" % (mydir, ss))
    copyfile("colorized_unw.png.aux.xml", "../../../PRODUCT/%s_%s_unw_phase.png.aux.xml" % (mydir, ss))
    copyfile("colorized_unw_large.png", "../../../PRODUCT/%s_%s_unw_phase_large.png" % (mydir, ss))
    copyfile("colorized_unw_large.png.aux.xml", "../../../PRODUCT/%s_%s_unw_phase_large.png.aux.xml" % (mydir, ss))
    copyfile("colorized_unw.kmz", "../../../PRODUCT/%s_%s_unw_phase.kmz" % (mydir, ss))
    copyfile("color.png", "../../../PRODUCT/%s_%s_color_phase.png" % (mydir, ss))
    copyfile("color.png.aux.xml", "../../../PRODUCT/%s_%s_color_phase.png.aux.xml" % (mydir, ss))
    copyfile("color_large.png", "../../../PRODUCT/%s_%s_color_phase_large.png" % (mydir, ss))
    copyfile("color_large.png.aux.xml", "../../../PRODUCT/%s_%s_color_phase_large.png.aux.xml" % (mydir, ss))
    copyfile("color.kmz", "../../../PRODUCT/%s_%s_color_phase.kmz" % (mydir, ss))
    copyfile("phase.tif", "../../../PRODUCT/%s_%s_unw_phase.tif" % (mydir, ss))
    copyfile("amp.tif", "../../../PRODUCT/%s_%s_amp.tif" % (mydir, ss))
    copyfile("coherence.tif", "../../../PRODUCT/%s_%s_corr.tif" % (mydir, ss))
    os.chdir("../../../")


def make_metadata_file(basedir, ss):
    # Get the platform heading
    back = os.getcwd()
    for mydir in os.listdir("."):
        if ".SAFE" in mydir and os.path.isdir(mydir):
            os.chdir("%s/annotation" % mydir)
            for myfile in os.listdir("."):
                if "001.xml" in myfile:
                    root = etree.parse(myfile)
                    for head in root.iter('platformHeading'):
                        heading = float(head.text)
                        print("Found heading %s" % heading)
                        break
                    else:
                        continue
                    break
            else:
                continue
            break
    os.chdir(back)

    baseline = ''
    utctime = ''
    heading = ''
    rg_looks = ''
    az_looks = ''

    os.chdir("%s/%s" % (basedir, ss))
    with open('isce.log', 'r') as g:
        for line in g.readlines():
            if "subset.Overlap" in line and "start time" in line:
                # FIXME: Too many steps here and re module is overkill
                t = re.split('=', line)
                t = t[1].strip()
                print("Found utctime %s" % t)
                t = re.split(' ', t)
                s = re.split(":", t[1])
                utctime = ((int(s[0]) * 60 + int(s[1])) * 60) + float(s[2])
            if "Bperp at midrange for first common burst" in line:
                t = re.split('=', line)
                baseline = t[1].strip()
                print("Found baseline %s" % baseline)
            if "geocode.Azimuth looks" in line:
                t = re.split('=', line)
                az_looks = t[1].strip()
                print("Found azimuth looks %s" % az_looks)
            if "geocode.Range looks" in line:
                t = re.split('=', line)
                rg_looks = t[1].strip()
                print("Found range looks %s" % rg_looks)
    os.chdir("../..")

    with open('PRODUCT/%s_%s.txt' % (basedir, ss), 'w') as f:
        f.write("baseline: %s\n" % baseline)
        f.write("utctime: %s\n" % utctime)
        f.write("heading: %s\n" % heading)
        f.write("range looks: %s\n" % rg_looks)
        f.write("azimuth looks: %s\n" % az_looks)


def proc_s1_stack_isce(csv_file=None, dem=False, roi=None, ss=None):
    """Main process

        csv_file = input file to read granules from and use get_asf.py
        dem      = If true, use get_dem instead of opentopo
        roi      = Region of interest, defined as (south north west east)
        ss       = Subswath to process

        roi and ss are mutually exclusive required parameters.
    """
    if roi is None and ss is None:
        print("ERROR: must specify one of ROI or SS")
        sys.exit(1)
    if roi is not None and ss is not None:
        print("ERROR: can only specify one of ROI or SS")
        sys.exit(1)

    options = {}

    if ss is not None:
        options['swath'] = int(ss)

    if csv_file is not None:
        file_subroutines.prepare_files(csv_file)

    (filenames, filedates) = file_subroutines.get_file_list()

    print(filenames)
    print(filedates)

    if roi is None:
        mydir = "%s/annotation" % filenames[0]
        myxml = ""
        name = ""
        if options['swath'] == 1:
            name = "001.xml"
        elif options['swath'] == 2:
            name = "002.xml"
        elif options['swath'] == 3:
            name = "003.xml"
        else:
            print("Invalid sub-swath specified %s" % options['swath'])

        for myfile in os.listdir(mydir):
            if name in myfile:
                myxml = "%s/annotation/%s" % (filenames[0], myfile)
        print("Found annotation file %s" % myxml)

        lat_max, lat_min, lon_max, lon_min = getSubSwath.get_bounding_box(myxml)

        options['south'] = lat_min
        options['north'] = lat_max
        options['west'] = lon_min
        options['east'] = lon_max
    else:
        options['south'] = roi[0]
        options['north'] = roi[1]
        options['west'] = roi[2]
        options['east'] = roi[3]

        # We were given a ROI, calculate the subswath
        options['swath'], roi = getSubSwath.SelectSubswath(filenames[0], options['west'], options['south'],
                                                           options['east'], options['north'])
        if options['swath'] == 0:
            sys.exit("ERROR: No overlap of bounding box with imagery")
        print("Found subswath %s to process" % options['swath'])

        options['south'] = roi[0]
        options['north'] = roi[1]
        options['west'] = roi[2]
        options['east'] = roi[3]

    if dem:
        get_ISCE_dem(options['west'], options['south'], options['east'], options['north'], "stack_dem.dem",
                     "stack_dem.dem.xml")
        options['demname'] = "stack_dem.dem"

    length = len(filenames)

    # Make XML files for pairs and 2nd pairs
    for x in range(length - 2):
        make_dir_and_xml(filedates[x], filedates[x + 1], filenames[x], filenames[x + 1], dem, options)
        make_dir_and_xml(filedates[x], filedates[x + 2], filenames[x], filenames[x + 2], dem, options)

    # If we have anything to process
    if length > 1:
        # Make XML files for last pair
        make_dir_and_xml(filedates[length - 2], filedates[length - 1], filenames[length - 2], filenames[length - 1],
                         dem, options)

        if not os.path.exists("PRODUCT"):
            os.mkdir("PRODUCT")

        # Run through directories processing imgs and collecting results as we go
        for mydir in os.listdir("."):
            if len(mydir) == 31 and os.path.isdir(mydir) and "_20" in mydir:
                print("Processing directory %s" % mydir)
                ss = 'iw' + str(options['swath'])
                isce_process(mydir, ss, " ")
                if os.path.isdir("%s/%s/merged" % (mydir, ss)):
                    print("Collecting directory %s" % mydir)
                    get_image_files(mydir, ss, options)
                    make_metadata_file(mydir, ss)


def main():
    """Main entrypoint"""

    # entrypoint name can differ from module name, so don't pass 0-arg
    cli_args = sys.argv[1:] if len(sys.argv) > 1 else None
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description=__doc__,
    )
    parser.add_argument("-f", "--csv-file",
                        help="Input CSV file of granules, otherwise process all SAFE files in the current directory")
    parser.add_argument("-d", "--dem", action="store_true",
                        help="Use get_dem to get the DEM file instead of opentopo")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-r", "--roi", nargs=4, type=float,
                       help="Set geocoding bounding box (south north west east), otherwise calculate "
                            "bounding box from first image")
    group.add_argument("-s", "--ss",
                       help="Set the subswath to process. If ROI is specified, calculate subswath")
    parser.add_argument('--version', action='version', version='hyp3insarisce {}'.format(__version__))
    args = parser.parse_args(cli_args)

    proc_s1_stack_isce(csv_file=args.csv_file, dem=args.dem, roi=args.roi, ss=args.ss)


if __name__ == "__main__":
    main()
