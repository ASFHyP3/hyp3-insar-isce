#!/usr/bin/env python
""" Wrapper script for processing Sentinel-1 with ISCE"""

from __future__ import print_function

import argparse
import os
import re
import shutil

from hyp3lib.execute import execute
from hyp3lib.get_orb import downloadSentinelOrbitFile
from lxml import etree

_HERE = os.path.abspath(os.path.dirname(__file__))


def createBaseDir(bname):
    if not os.path.exists(bname):
        os.mkdir(bname)


def prepDirISCE(bname, ss):
    os.chdir(bname)
    if not os.path.exists(ss):
        os.mkdir(ss)
    os.chdir("..")


def createISCEXML(g1, g2, f1, f2, options):
    template = os.path.join(_HERE, 'etc', 'isceS1template.xml')
    root = etree.parse(template)

    comp = root.find('component')
    for c in comp.findall('property'):
        if c.attrib['name'] == 'do unwrap':
            c.text = str(options['unwrap'])

    if options['gbb']:
        gbb = etree.Element('property', name='geocode bounding box')
        gbb.text = '[{}, {}, {}, {}]'.format(
            options['gbb_south'], options['gbb_north'], options['gbb_west'], options['gbb_east']
        )
        comp.append(gbb)

    if options['dem']:
        dem = etree.Element('property', name='demfilename')
        dem.text = str(os.path.abspath(options['demname']))
        comp.append(dem)

    for comp in root.findall('component/component'):
        if comp.attrib['name'] == 'master':
            for c in comp.findall('property'):
                if c.attrib['name'] == 'safe':
                    c.text = os.path.abspath(g1)
                if c.attrib['name'] == 'orbit file':
                    c.text = f1
                if c.attrib['name'] == 'swath number':
                    c.text = str(options['swath'])

            if options['roi']:
                roi = etree.Element('property', name='region of interest')
                roi.text = '[{}, {}, {}, {}]'.format(
                    options['south'], options['north'], options['west'], options['east']
                )
                comp.append(roi)

        if comp.attrib['name'] == 'slave':
            for c in comp.findall('property'):
                if c.attrib['name'] == 'safe':
                    c.text = os.path.abspath(g2)
                if c.attrib['name'] == 'orbit file':
                    c.text = f2
                if c.attrib['name'] == 'swath number':
                    c.text = str(options['swath'])

            if options['roi']:
                roi = etree.Element('property', name='region of interest')
                roi.text = '[{}, {}, {}, {}]'.format(
                    options['south'], options['north'], options['west'], options['east']
                )
                comp.append(roi)

    outfile = os.path.join(options['bname'], options['ss'], 'topsApp.xml')
    with open(outfile, 'wb') as of:
        of.write(b'<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n')
        root.write(of, pretty_print=True)


def iscePreProcess(bname, ss):
    cmd = 'cd {bname}/{ss} ; ' \
          'source activate isce; ' \
          'source ~/.isce/.isceenv; ' \
          'topsApp.py --end=preprocess'.format(bname=bname, ss=ss)
    execute(cmd)


def isceCalibration(bname, ss):
    pass


def isceProcess(bname, ss, step):
    cmd = 'cd {bname}/{ss} ; topsApp.py {step}'.format(bname=bname, ss=ss, step=step)
    execute(cmd)


def procS1ISCE(ss, masterSafe, slaveSafe, gbb=None, xmlFlag=None, unwrapFlag=None, demFile=None):
    """Main Entry Point:

          ss         = subswath to process
          masterSafe = master SAFE file
          slaveSafe  = slave SAFE file
          gbb        = set a geocoding bounding box
          xmlFlag    = if True, only create XML file, do not run
          unwrapFlag = if True, turn on unwrapping
          demFile    = Specify external DEM file to use
    """
    options = {'unwrap': False, 'roi': False, 'proc': True, 'gbb': False, 'dem': False}

    if unwrapFlag:
        options['unwrap'] = True

    if gbb is not None:
        options['gbb'] = True
        options['gbb_south'] = gbb[0]
        options['gbb_north'] = gbb[1]
        options['gbb_west'] = gbb[2]
        options['gbb_east'] = gbb[3]

    if xmlFlag:
        options['proc'] = False

    if demFile is not None:
        options['dem'] = True
        options['demname'] = demFile

    # g1 and g2 are the two granules that we are processing
    g1 = masterSafe
    g2 = slaveSafe

    t = re.split('_+', g1)
    md = t[4][0:16]
    t = re.split('_+', g2)
    sd = t[4][0:16]

    bname = '%s_%s' % (md, sd)
    ssname = 'iw'+str(ss)

    options['bname'] = bname
    options['ss'] = ssname
    options['swath'] = ss

    print(g1, g2, options)

    # Create our base and iwX dir
    createBaseDir(bname)
    prepDirISCE(bname, ssname)

    # Pull the orbit files and put them in the proper directory
    destDir = os.path.join(bname, ssname)

    orbFileName1, tmp = downloadSentinelOrbitFile(g1)
    shutil.move(orbFileName1, destDir)

    orbFileName2, tmp = downloadSentinelOrbitFile(g2)
    shutil.move(orbFileName2, destDir)

    createISCEXML(g1, g2, orbFileName1, orbFileName2, options)

    # Process through preprocess
    # iscePreProcess(bname, ssname)

    # This routine will calibrate the SLCs (eventually)
    # isceCalibration(bname, ssname)

    # Process through filter
    # isceProcess(bname, ssname, '--start=computeBaselines --end=filter')

    # Unwrap if requested
    # if options['unwrap'] == True:
    #     isceProcess(bname, ssname, ' --dostep=unwrap')

    # do final geocode
    # step = ' --dostep=geocode'
    # isceProcess(bname, ssname, step)

    if options['proc']:
        isceProcess(bname, ssname, '')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an Sentinel-1 interferogram using ISCE software")
    parser.add_argument("-x", "--xml", action="store_true", help="Only create XML file,  do not run")
    parser.add_argument("-u", "--unwrap", action="store_true", help="Unwrap the phase; default is no unwrapping")
    parser.add_argument("-g", "--gbb", nargs=4, type=float, help="Set geocoding bounding box (south north west east)")
    parser.add_argument("-d", "--dem", help="Specify external DEM file to be used")
    parser.add_argument("-s", "--ss", required=True, help="Set subswath to process")
    parser.add_argument("masterSafe", metavar="masterSafe", help="Master SAFE file")
    parser.add_argument("slaveSafe", metavar="slaveSafe", help="Slave SAFE file")
    args = parser.parse_args()
    procS1ISCE(
        args.ss, args.masterSafe, args.slaveSafe,
        gbb=args.gbb, xmlFlag=args.xml, unwrapFlag=args.unwrap, demFile=args.dem
    )
