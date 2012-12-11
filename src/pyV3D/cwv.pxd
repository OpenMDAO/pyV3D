
# file: cwv.pxd

cdef extern from "cwv.h":

  wvContext* wv_createContext(int bias, float fov, float zNear, float zFar, float *eye,
                               float *center, float *up)
