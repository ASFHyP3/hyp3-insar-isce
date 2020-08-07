# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [PEP 440](https://www.python.org/dev/peps/pep-0440/) 
and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0](https://github.com/ASFHyP3/hyp3-insar-isce/compare/v0.0.0...v1.0.0)

This is a significant refactor of `hyp3-insar-isce` into:
* A `pip` installable package called `hyp3_insar_isce`
* A stand alone, container-based HyP3 plugin

**NOTE:** There are significant changes to the overall repository structure that
will break all existing HyP3 workflows!

### Removed
* Python 2. This package now requires python 3.7+
* Output GeoTIFFs no longer have overviews
* This drops the low-res browse images from the output product package
  * formerly `*.png` was low-res and `*_large.png` was high-res. Now, `*.png` is
    a high-res browse image and `*_large.png` files are no longer produced
* No longer supports the GIMP, REMA, and EU DEMs (due to them being dropped in `hyp3lib`)

### Added
 A packaging and testing structure -- now pip installable and testing is done via pytest
  * Previous command line scripts are now registered entrypoints and created when the 
    package is `pip` installed:
    * `procAllS1StackISCE.py`
    * `procS1ISCE.py`
    * `procS1StackISCE.py`
* A Dockerfile to build the HyP3 plugin
* A CI/CD workflow setup, which will build and publish the docker container
* The processing script that used to live in the now depreciated `cloud-proj` repository 
  has been moved into the package as `hyp3_insar_isce.__main__` and also registered 
  as a `hyp3_insar_isce` entrypoint
* A `conda-env.yml` to create conda environments for testing and running in the docker container
* The version numbers tracked automatically via git tags


### Changed
* All of `src/` is now contained in the `hyp3_insar_isce` package
* All of `etc/` is now contained in `hyp3_insar_isce.etc`
