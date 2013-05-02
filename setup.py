import sys
import os
import setuptools

try:
    from numpy.distutils.core import setup
    from numpy.distutils.misc_util import Configuration
except ImportError:
    print 'numpy was not found.  Aborting build'
    sys.exit(-1)

srcs = [
    "src/pyV3D/_pyV3D.c",
    "src/pyV3D/wv.c"
]

config = Configuration(name="pyV3D")
config.add_extension("_pyV3D", sources=srcs)

kwds = {'version': '0.4',
        'install_requires':['numpy', 'tornado', 'argparse'],
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
               'pyV3D': ['test/*.py', 'test/*.csm', 'test/*.col']
        },
        'package_dir': {'': 'src'},
        'packages': ['pyV3D'],
        'url': 'https://github.com/OpenMDAO/pyV3D',
        'zip_safe': False,
       }

kwds.update(config.todict())

setup(**kwds)

