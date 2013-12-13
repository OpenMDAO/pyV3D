README.txt file for pyV3D.

pyV3D is a python library that will take data that describes a geometry (like
arrays of vertices, triangles, colors, and possibly normals) and convert
that into an efficient binary format that can be sent to a browser where
the geometry will be rendered using WebGL.

To install:
    'python setup.py install'

If you intend to do pyV3D development:
    python setup.py develop

Installing this package does not require cython. If you have cython
installed, it will automatically be used to build pyV3D. If you do not have
cython installed and wish to change the pyV3D cython code 
(src/pyV3D/_pyV3D.pyx),then you will need to install cython and run it on the
file before running 'python setup.py install'.

Note: wvserver.py and the accompanying wvclient code have been removed from the
package. To obtain the code, you will need git to 

    1. Clone pyV3D:
        'git clone https://github.com/OpenMDAO/pyV3D'

    2. Checkout a previous commit that you are interested in
    
        For pyV3D with wvclient code only
            'git checkout -b with-wvclient tags/with-wvclient'

        For pyV3d with wvclient and wvserver.py
            'git checkout -b with-wvserver tags/with-wvserver'

