
import os
import sys
import struct

from numpy import array, float32, float64, int32, uint8
import numpy as np

from pyV3D.handlers import WV_ViewHandler

from PAM.configurations.pyv3d import GeoMACHParametricGeometry

class GeoMACHViewHandler(WV_ViewHandler):

    @staticmethod
    def get_file_extensions():
        """Returns a list of file extensions that this handler knows how to view."""
        return ['py']   #FIXME: using py extension here is probably not a great idea

    def create_geom(self):
        DEBUG("create_geom")
        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)
        fov   = 30.0
        zNear = 1.0
        zFar  = 10.0

        bias  = 1
        self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)

        self.my_param_geom = GeoMACHParametricGeometry(self.modpath)
        geom = self.my_param_geom.get_geometry()
        if geom is None:
            raise RuntimeError("can't get Geometry object")
        geom.get_visualization_data(self.wv)

