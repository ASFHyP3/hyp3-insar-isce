import os

from setuptools import find_packages, setup

_HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(_HERE, 'README.md'), 'r') as f:
    long_desc = f.read()

setup(
    name='hyp3_insar_isce',
    use_scm_version=True,
    description='HyP3 plugin for InSAR processing with ISCE',
    long_description=long_desc,
    long_description_content_type='text/markdown',

    url='https://github.com/ASFHyP3/hyp3-insar-isce',

    author='ASF APD/Tools Team',
    author_email='uaf-asf-apd@alaska.edu',

    license='BSD',
    include_package_data=True,

    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        ],

    python_requires='~=3.7',

    install_requires=[
        'hyp3lib==1.4.1',
        'hyp3proclib~=1.0',
        'importlib_metadata',
        'lxml',
    ],

    extras_require={
        'develop': [
            'pytest',
            'pytest-cov',
            'pytest-console-scripts',
        ]
    },

    packages=find_packages(),

    entry_points={'console_scripts': [
        'hyp3_insar_isce = hyp3_insar_isce.__main__:main',
        'procAllS1StackISCE.py = hyp3_insar_isce.proc_all_s1_stack_isce:main',
        'procS1ISCE.py = hyp3_insar_isce.proc_s1_isce:main',
        'procS1StackISCE.py = hyp3_insar_isce.proc_s1_stack_isce:main',
        ]
    },

    zip_safe=False,
)
