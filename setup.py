
#from numpy.distutils.core import Extension, setup
#from numpy.distutils.misc_util import Configuration
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("cwv", ["src/pyV3D/cwv.pxd"]),
                   Extension("wv", ["src/pyV3D/wv.c"])]
)

##from numpy.distutils.core import Extension, setup
##from numpy.distutils.misc_util import Configuration
#from distutils.core import setup
#from distutils.extension import Extension
#from Cython.Distutils import build_ext

#ext_modules = [Extension("pyV3D", ["src/pyV3D/pyV3D.pyx"])]

#kwargs = {'author': '',
 #'author_email': '',
 #'classifiers': ['Intended Audience :: Science/Research',
                 #'Topic :: Scientific/Engineering'],
 #'cmd_class' : {'build_ext': build_ext},
 #'description': '',
 #'download_url': '',
 #'ext_modules' : ext_modules,
 #'include_package_data': True,
 #'install_requires': ['openmdao.main'],
 #'keywords': ['openmdao'],
 #'license': '',
 #'maintainer': '',
 #'maintainer_email': '',
 #'name': 'pyV3D',
 #'package_data': {'pyV3D': []},
 #'package_dir': {'': 'src'},
 #'packages': ['pyV3D'],
 #'url': '',
 #'version': '0.1',
 #'zip_safe': False}


#setup(**kwargs)

