"""Create a Sentinel-1 interferogram using ISCE software"""

import argparse
import os
import re

from hyp3lib.execute import execute
from hyp3lib.file_subroutines import mkdir_p
from hyp3lib.get_orb import downloadSentinelOrbitFile
from lxml import etree

from hyp3_insar_isce import __version__

_HERE = os.path.abspath(os.path.dirname(__file__))


def create_isce_xml(g1, g2, f1, f2, options):
    root = etree.parse(os.path.join(_HERE, 'etc', 'isceS1template.xml'))

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


def proc_s1_isce(ss, reference, secondary, gbb=None, xml=False, unwrap=False, dem=None):
    """Main process

          ss        = subswath to process
          reference = reference SAFE file
          secondary = secondary SAFE file
          gbb       = set a geocoding bounding box (south north west east)
          xml       = if True, only create XML file, do not run
          unwrap    = if True, turn on unwrapping
          dem       = Specify external DEM file to use
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
    g1 = reference
    g2 = secondary

    t = re.split('_+', g1)
    md = t[4][0:16]
    t = re.split('_+', g2)
    sd = t[4][0:16]

    bname = '%s_%s' % (md, sd)
    ssname = 'iw'+str(ss)
    isce_dir = os.path.join(bname, ssname)

    options['bname'] = bname
    options['ss'] = ssname
    options['swath'] = ss

    print(g1, g2, options)

    mkdir_p(bname)
    mkdir_p(isce_dir)

    g1_orbit_file, _ = downloadSentinelOrbitFile(g1, directory=isce_dir)
    g2_orbit_file, _ = downloadSentinelOrbitFile(g2, directory=isce_dir)

    create_isce_xml(g1, g2, os.path.basename(g1_orbit_file), os.path.basename(g2_orbit_file), options)

    # execute(f'cd {isce_dir} ; topsApp.py --end=preprocess')

    # execute(f'cd {isce_dir} ; topsApp.py --start=computeBaselines --end=filter')

    # if options['unwrap'] == True:
    #     execute(f'cd {isce_dir} ; topsApp.py --dostep=unwrap')

    # execute(f'cd {isce_dir} ; topsApp.py --dostep=geocode')

    if options['proc']:
        execute(f'cd {isce_dir} ; topsApp.py')


def main():
    """Main entrypoint"""
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description=__doc__,
    )
    parser.add_argument("ss", help="Set subswath to process")
    parser.add_argument("reference", help="Reference SAFE file")
    parser.add_argument("secondary", help="Secondary SAFE file")
    parser.add_argument("-g", "--gbb", nargs=4, type=float, help="Set geocoding bounding box (south north west east)")
    parser.add_argument("-x", "--xml", action="store_true", help="Only create XML file,  do not run")
    parser.add_argument("-u", "--unwrap", action="store_true", help="Unwrap the phase; default is no unwrapping")
    parser.add_argument("-d", "--dem", help="Specify external DEM file to be used")
    parser.add_argument('--version', action='version', version=f'hyp3_insar_isce {__version__}')
    args = parser.parse_args()

    proc_s1_isce(
        args.ss, args.reference, args.secondary,
        gbb=args.gbb, xml=args.xml, unwrap=args.unwrap, dem=args.dem
    )


if __name__ == "__main__":
    main()
