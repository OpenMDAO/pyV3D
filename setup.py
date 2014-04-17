import sys
import setuptools
import os

try:
    from numpy.distutils.core import setup
    from numpy.distutils.misc_util import Configuration
except ImportError:
    print 'numpy was not found.  Aborting build'
    sys.exit(-1)

kwds = {'version': '0.4.4',
        'install_requires': ['numpy', 'tornado', 'argparse'],
        'author': '',
        'author_email': '',
        'classifiers': ['Intended Audience :: Science/Research',
                        'Topic :: Scientific/Engineering'],
        'description': 'Python webGL based 3D viewer',
        'download_url': '',
        'include_package_data': True,
        'keywords': ['openmdao'],
        'license': 'Apache License, Version 2.0',
        'maintainer': 'Kenneth T. Moore',
        'maintainer_email': 'kenneth.t.moore-1@nasa.gov',
        'package_data': {
            'pyV3D': ['wvclient/*.html', 'wvclient/WebViewer/*.js'],
            'pyV3D.test': ['*.stl', '*.bin']
        },
        'package_dir': {'': 'src'},
        'packages': ['pyV3D', 'pyV3D.test'],
        'url': 'https://github.com/OpenMDAO/pyV3D',
        'zip_safe': False,
        'entry_points': {
            'console_scripts': [
               "wvserver=pyV3D.wvserver:main"
            ]
        }}

USE_CYTHON = False
srcs = [os.path.join("src", "pyV3D", "_pyV3D.c"),
        os.path.join("src", "pyV3D", "wv.c"),
        ]

if sys.argv[1] == "develop":
    USE_CYTHON = True
    srcs[0] = "{}{}".format(srcs[0][:-2], ".pyx")
    
config = Configuration(name="pyV3D")
config.add_extension("_pyV3D", sources=srcs)
kwds.update(config.todict())

if USE_CYTHON:
    from Cython.Build import cythonize
    kwds["ext_modules"] = cythonize(kwds['ext_modules'])

setup(**kwds)
