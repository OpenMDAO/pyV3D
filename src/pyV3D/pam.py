
import os
import sys
import struct

from numpy import array, float32, float64, int32, uint8
import numpy as np

from pyV3D.handlers import WV_ViewHandler

from PAM.configurations.pyv3d import GeoMACHParametricGeometry

def get_module_path(fpath):
    """Given a module filename, return its full Python name including
    enclosing packages. (based on existence of ``__init__.py`` files)
    """
    if os.path.basename(fpath).startswith('__init__.'):
        pnames = []
    else:
        pnames = [os.path.splitext(os.path.basename(fpath))[0]]
    path = os.path.dirname(os.path.abspath(fpath))
    while os.path.isfile(os.path.join(path, '__init__.py')):
            path, pname = os.path.split(path)
            pnames.append(pname)
    return '.'.join(pnames[::-1])

class GeoMACHViewHandler(WV_ViewHandler):

    @staticmethod
    def get_file_extensions():
        """Returns a list of file extensions that this handler knows how to view."""
        return ['py']   #FIXME: using py extension here is probably not a great idea

    def create_geom(self):
        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)
        fov   = 30.0
        zNear = 1.0
        zFar  = 10.0

        bias  = 1
        self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)

        modpath = get_module_path(self.geometry_file)
        sys.stderr.write("total = %s\n" % ('.'.join([modpath, self.inner_class])))
        self.my_param_geom = GeoMACHParametricGeometry('.'.join([modpath, self.inner_class]))
        geom = self.my_param_geom.get_geometry()
        if geom is None:
            raise RuntimeError("can't get Geometry object")
        geom.get_visualization_data(self.wv)

