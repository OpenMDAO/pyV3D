import os.path
import setuptools
import sys

from numpy.distutils.core import setup
from numpy.distutils.misc_util import Configuration

include_dirs = []
library_dirs = []
if sys.platform == 'win32':
    # Update the ``library_dir_option`` function in MSVCCompiler 
    # to add quotes around /LIBPATH entries.
    import types
    def _lib_dir_option(self, dir):
        return '/LIBPATH:"%s"' % dir
    
    from distutils.msvc9compiler import MSVCCompiler
    setattr(MSVCCompiler, 'library_dir_option',
            types.MethodType(_lib_dir_option, None, MSVCCompiler))
    
    sdkdir = os.environ.get('WindowsSdkDir')
    if sdkdir:
        include_dirs.append(os.path.join(sdkdir,'Include'))
        library_dirs.append(os.path.join(sdkdir,'Lib'))
        # make sure we have mt.exe available in case we need it
        path = os.environ['PATH'].split(';')
        path.append(os.path.join(sdkdir,'bin'))
        os.environ['PATH'] = ';'.join(path)

config = Configuration(name='pyV3D')
config.add_extension('_pyV3D',
                     sources=['src/pyV3D/wv.c', 'src/pyV3D/_pyV3D.c'],
                     include_dirs=include_dirs,
                     library_dirs=library_dirs)
config.add_data_files('LICENSE.txt','README.txt')

kwds = {'install_requires':['numpy', 'tornado', 'argparse'],
        'author': '',
        'author_email': '',
        'classifiers': ['Intended Audience :: Science/Research',
                        'Topic :: Scientific/Engineering'],
        'description': 'Python web viewer for VBOs',
        'download_url': '',
        'include_package_data': True,
        'keywords': ['openmdao'],
        'license': 'Apache License, Version 2.0',
        'maintainer': 'Kenneth T. Moore',
        'maintainer_email': 'kenneth.t.moore-1@nasa.gov',
        'name': 'pyV3D',
        'package_data': {'pyV3D': []},
        'package_dir': {'': 'src'},
        'packages': ['pyV3D'],
        'url': 'https://github.com/OpenMDAO/pyV3D',
        'version': '0.1',
        'zip_safe': False,
        'entry_points': """
           [pyv3d.subhandlers]
           pyV3D.stl.STLViewHandler = pyV3D.stl:STLViewHandler
           pyV3D.pam.GeoMACHViewHandler = pyV3D.pam:GeoMACHViewHandler
        """
       }

kwds.update(config.todict())
setup(**kwds)




#from numpy.distutils.core import Extension, setup
#from numpy.distutils.misc_util import Configuration
#from distutils.core import setup
#from distutils.extension import Extension
#from Cython.Distutils import build_ext
#
#setup(
#    cmdclass = {'build_ext': build_ext},
#    ext_modules = [Extension("wv", ["src/pyV3D/wv.c"]),
#                   Extension("pyV3D", ["src/pyV3D/pyV3D.pyx"])]
#)
