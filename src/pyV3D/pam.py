
from numpy import array, float32

from pyV3D.handlers import WV_Sender

from PAM.configurations.pyv3d import GeoMACHParametricGeometry, GeoMACHGeometry


class GeoMACHSender(WV_Sender):

    def initialize(self, **kwargs):
        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)
        fov   = 30.0
        zNear = 1.0
        zFar  = 10.0

        bias  = 0
        self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)

    @staticmethod
    def supports(obj):
        return isinstance(obj, GeoMACHGeometry) or isinstance(obj, GeoMACHParametricGeometry)

    def geom_from_obj(self, obj):
        if isinstance(obj, GeoMACHParametricGeometry):
            obj = obj.get_geometry()
            if obj is None:
                raise RuntimeError("can't get Geometry object from GeoMACHParametricGeometry")
        elif not isinstance(obj, GeoMACHGeometry):
            raise TypeError("object must be a GeoMACHParametricGeometry or GeoMACHGeometry but is a '%s' instead" %
                str(type(obj)))
        obj.get_visualization_data(self.wv)

