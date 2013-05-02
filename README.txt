README.txt file for pyV3D.

pyV3D has two parts.  

One part is a python library
that will take data that describes a geometry (like
arrays of vertices, triangles, colors, and possibly normals) and convert
that into an efficient binary format that can be sent to a browser where
the geometry will be rendered using WebGL.

The other part is a javascript library that takes that binary data created
using the python library and uses it to create a WebGL scene graph and 
display it.

The pyV3D distribution contains a simple tornado server that will allow 
you to view geometries from STL files.  It also has a built-in geometry 
for a simple cube for demo purposes if you don't happen to have any STL
files handy.  To run the server (after installing pyV3D), just type:


   wvserver


Here are the command line options for the server:


usage: wvserver [-h] [-p PORT] [--logging LOGGING] [viewdir]

launch the test server

positional arguments:
  viewdir               pathname of directory containing files to view

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  port to run server on
  --logging LOGGING     set logging level, e.g., --logging=info or
                        --logging=debug


The pyV3D test directory contains a few sample STL files for viewing.

After the server is running, point your browser to localhost:8000 (or to whatever
port number you've specified with the --port command line option) and you should
be prompted for a filename.  Click OK without entering any text to see the simple
cube.  To view an STL file, enter the name of the file, relative to the viewdir
directory you specified when you ran the server.  You will only be able to view
files that are under the viewdir directory.

Once the image is displayed, you can rotate it by holding down CTRL and left clicking
and dragging the mouse.  SHIFT + left click and drag will zoom the image.


Note: installing this package does not require cython. If you wish to change
the pyV3D cython code, then you will need to install cython and run it on the src/pyV3D/_pyV3D.pyx file before running 'python setup.py build'.


