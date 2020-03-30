#!/usr/bin/env python
import datetime
import os
import shutil

from hyp3proclib import (
    build_output_name_pair,
    earlier_granule_first,
    failure,
    find_browses,
    find_phase_png,
    get_extra_arg,
    get_looks,
    process,
    record_metrics,
    success,
    upload_product,
    zip_dir
)
from hyp3proclib.db import get_db_connection
from hyp3proclib.file_system import add_citation, cleanup_workdir
from hyp3proclib.logger import log
from hyp3proclib.proc_base import Processor

import hyp3insarisce


def write_list_file(list_file, g1, g2):
    with open(list_file, 'w') as f:
        f.write(g1 + '\n')
        f.write(g2 + '\n')


def find_subswath(dir_):
    sub = next(os.walk(dir_))[1][0]
    log.debug('Subswath dir: ' + sub)
    return sub


def process_insar(cfg, n):
    try:
        log.info('Processing ISCE InSAR pair "{0}" for "{1}"'.format(cfg['sub_name'], cfg['username']))

        g1, g2 = earlier_granule_first(cfg['granule'], cfg['other_granules'][0])

        list_file = 'list.csv'
        write_list_file(os.path.join(cfg['workdir'], list_file), g1, g2)

        d1 = g1[17:25]
        d2 = g2[17:25]
        delta = (datetime.datetime.strptime(d2, '%Y%m%d')-datetime.datetime.strptime(d1, '%Y%m%d')).days
        ifm_dir = d1 + '_' + d2
        cfg['ifm'] = ifm_dir
        log.debug('IFM dir is: ' + ifm_dir)

        sd1 = d1[0:4]+'-'+d1[4:6]+'-'+d1[6:8]
        sd2 = d2[0:4]+'-'+d2[4:6]+'-'+d2[6:8]
        cfg["email_text"] = "This is a {0}-day InSAR pair from {1} to {2}.".format(delta, sd1, sd2)

        subswath = get_extra_arg(cfg, "subswath", "0")
        if subswath == "0":
            process(cfg, 'procAllS1StackISCE.py', ["-90", "90", "-180", "180", "-f", list_file, "-d"])
        else:
            process(cfg, 'procS1StackISCE.py', ["-f", list_file, "-d", "-s", subswath])

        subdir = os.path.join(cfg['workdir'], 'PRODUCT')
        if not os.path.isdir(subdir):
            log.info('PRODUCT directory not found: ' + subdir)
            log.error('Processing failed')
            raise Exception("Processing failed: PRODUCT directory not found")
        else:
            looks = get_looks(subdir)
            out_name = build_output_name_pair(g1, g2, cfg['workdir'], looks + "-iw" + subswath + cfg['suffix'])
            log.info('Output name: ' + out_name)

            out_path = os.path.join(cfg['workdir'], out_name)
            zip_file = out_path + '.zip'
            if os.path.isdir(out_path):
                shutil.rmtree(out_path)
            if os.path.isfile(zip_file):
                os.unlink(zip_file)
            cfg['out_path'] = out_path

            # clip_tiffs_to_roi(cfg, conn, product)

            log.debug('Renaming '+subdir+' to '+out_path)
            os.rename(subdir, out_path)

            find_browses(cfg, out_path)

            cfg['attachment'] = find_phase_png(out_path)
            add_citation(cfg, out_path)
            zip_dir(out_path, zip_file)

            cfg['final_product_size'] = [os.stat(zip_file).st_size, ]
            cfg['original_product_size'] = 0

            with get_db_connection('hyp3-db') as conn:
                record_metrics(cfg, conn)
                upload_product(zip_file, cfg, conn)
                success(conn, cfg)

    except Exception as e:
        log.exception('Processing failed')
        log.info('Notifying user')
        failure(cfg, str(e))

    cleanup_workdir(cfg)

    log.info('Done')


def main():
    processor = Processor('insar_isce', process_insar, sci_version=hyp3insarisce.__version__)
    processor.run()


if __name__ == "__main__":
    main()
