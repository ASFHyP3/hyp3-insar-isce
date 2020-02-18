#!/usr/bin/env python
"""Create a Sentinel-1 interferogram using ISCE software"""

from __future__ import print_function

import argparse
import os
import re
import shutil
import sys

from hyp3lib.execute import execute
from hyp3lib.get_orb import downloadSentinelOrbitFile_2
from lxml import etree

_HERE = os.path.abspath(os.path.dirname(__file__))


def create_base_dir(bname):
    if not os.path.exists(bname):
        os.mkdir(bname)


def prep_dir_isce(bname, ss):
    os.chdir(bname)
    if not os.path.exists(ss):
        os.mkdir(ss)
    os.chdir("..")


def create_isce_xml(g1, g2, f1, f2, options):
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


def isce_pre_process(bname, ss):
    cmd = 'cd {bname}/{ss} ; ' \
          'source activate isce; ' \
          'source ~/.isce/.isceenv; ' \
          'topsApp.py --end=preprocess'.format(bname=bname, ss=ss)
    execute(cmd)


def isce_process(bname, ss, step):
    cmd = 'cd {bname}/{ss} ; topsApp.py {step}'.format(bname=bname, ss=ss, step=step)
    execute(cmd)


def proc_s1_isce(ss, master, slave, gbb=None, xml=False, unwrap=False, dem=None):
    """Main process

          ss      = subswath to process
          master  = master SAFE file
          slave   = slave SAFE file
          gbb     = set a geocoding bounding box (south north west east)
          xml     = if True, only create XML file, do not run
          unwrap  = if True, turn on unwrapping
          dem     = Specify external DEM file to use
    """
    options = {'unwrap': unwrap, 'roi': False, 'proc': xml, 'gbb': False, 'dem': False}

    if gbb is not None:
        options['gbb'] = True
        options['gbb_south'] = gbb[0]
        options['gbb_north'] = gbb[1]
        options['gbb_west'] = gbb[2]
        options['gbb_east'] = gbb[3]

    if dem is not None:
        options['dem'] = True
        options['demname'] = dem

    # g1 and g2 are the two granules that we are processing
    g1 = master
    g2 = slave

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
    create_base_dir(bname)
    prep_dir_isce(bname, ssname)

    # Pull the orbit files and put them in the proper directory
    dest_dir = os.path.join(bname, ssname)

    orb_file_name1, tmp = downloadSentinelOrbitFile_2(g1)
    shutil.move(orb_file_name1, dest_dir)

    orb_file_name2, tmp = downloadSentinelOrbitFile_2(g2)
    shutil.move(orb_file_name2, dest_dir)

    create_isce_xml(g1, g2, orb_file_name1, orb_file_name2, options)

    # Process through preprocess
    # isce_pre_process(bname, ssname)

    # Process through filter
    # isce_process(bname, ssname, '--start=computeBaselines --end=filter')

    # Unwrap if requested
    # if options['unwrap'] == True:
    #     isce_process(bname, ssname, ' --dostep=unwrap')

    # do final geocode
    # step = ' --dostep=geocode'
    # isce_process(bname, ssname, step)

    if options['proc']:
        isce_process(bname, ssname, '')


def main():
    """Main entrypoint"""

    # entrypoint name can differ from module name, so don't pass 0-arg
    cli_args = sys.argv[1:] if len(sys.argv) > 1 else None
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description=__doc__,
    )
    parser.add_argument("ss", help="Set subswath to process")
    parser.add_argument("master", help="Master SAFE file")
    parser.add_argument("slave", help="Slave SAFE file")
    parser.add_argument("-g", "--gbb", nargs=4, type=float, help="Set geocoding bounding box (south north west east)")
    parser.add_argument("-x", "--xml", action="store_true", help="Only create XML file,  do not run")
    parser.add_argument("-u", "--unwrap", action="store_true", help="Unwrap the phase; default is no unwrapping")
    parser.add_argument("-d", "--dem", help="Specify external DEM file to be used")

    args = parser.parse_args(cli_args)

    proc_s1_isce(
        args.ss, args.master, args.slave,
        gbb=args.gbb, xml=args.xml, unwrap=args.unwrap, dem=args.dem
    )


if __name__ == "__main__":
    main()
