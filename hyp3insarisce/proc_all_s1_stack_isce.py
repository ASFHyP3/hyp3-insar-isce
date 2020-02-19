#!/usr/bin/env python
"""Create All interferograms overlapping the ROI using ISCE"""

from __future__ import print_function

import argparse
import os
import sys

from hyp3lib import __version__, getSubSwath
from hyp3lib.file_subroutines import get_file_list
from hyp3lib.file_subroutines import prepare_files

from hyp3insarisce.proc_s1_stack_isce import proc_s1_stack_isce


def proc_all_s1_stack_isce(south, north, west, east, csv_file=None, dem=None):
    """Main process

        south,north,west,east -- bounding box
        csv_file = file to fetch granules from using get_asf.py
        dem = if TRUE, use ASF get_dem instead of opentopo
    """
    # If file list is given, download the files and unzip them
    if csv_file is not None:
        prepare_files(csv_file)

    (filenames, filesdates) = get_file_list()

    swaths, roi = getSubSwath.SelectAllSubswaths(filenames[0], west, south, east, north)

    if len(swaths) == 0:
        sys.exit("ERROR: No overlap of bounding box with imagery")
    print("Found {} subswath(s) to process".format(len(swaths)))

    for subswath in swaths:
        proc_s1_stack_isce(dem=dem, ss=int(subswath))


def main():
    """Main entrypoint"""

    # entrypoint name can differ from module name, so don't pass 0-arg
    cli_args = sys.argv[1:] if len(sys.argv) > 1 else None
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description=__doc__,
    )
    parser.add_argument("south", help="Minimum latitude")
    parser.add_argument("north", help="Maximum latitude")
    parser.add_argument("west", help="Minimum longitude")
    parser.add_argument("east", help="Maximum longitude")
    parser.add_argument("-f", "--csv-file", help="list of files to download, in csv format")
    parser.add_argument("-d", "--dem", action="store_true", help="Use the ASF DEM heap instead of opentopo")
    parser.add_argument('--version', action='version', version='hyp3insarisce {}'.format(__version__))
    args = parser.parse_args(cli_args)

    proc_all_s1_stack_isce(args.south, args.north, args.west, args.east, csv_file=args.csv_file, dem=args.dem)


if __name__ == "__main__":
    main()
