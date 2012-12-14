
# file: cwv.pxd

from numpy import ndarray

cdef extern from "wv.h":

    ctypedef struct wvContext:
        pass

    wvContext* wv_createContext(int bias, float fov,
                                float zNear, float zFar, float *eye,
                                float *center, float *up)
