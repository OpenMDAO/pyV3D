import sys
import setuptools

try:
    from numpy.distutils.core import setup
    from numpy.distutils.misc_util import Configuration
except ImportError:
    print 'numpy was not found.  Aborting build'
    sys.exit(-1)

kwds = {'version': '0.4.2',
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

try:
    from Cython.Build import cythonize
except:
    USE_CYTHON = False
    file_extension = ".c"
else:
    USE_CYTHON = True
    file_extension = ".pyx"

srcs = [
    "src/pyV3D/_pyV3D{0}".format(file_extension),
    "src/pyV3D/wv.c"
]

config = Configuration(name="pyV3D")
config.add_extension("_pyV3D", sources=srcs)
kwds.update(config.todict())

if USE_CYTHON:
    kwds["ext_modules"] = cythonize(kwds['ext_modules'])
    
setup(**kwds)
