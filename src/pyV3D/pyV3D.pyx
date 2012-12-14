# file: pyV3D.pyx

cimport cwv
#from numpy import array
from array import array

cdef class pyV3D:

    def __init__(self):
        pass
        
    #def __cinit__(self):
    #    pass
        
    cdef test(self):
        ''' Playing around'''

        eye    = array([1.0, 0.0, 7.0])
        center = array([0.0, 0.0, 0.0])
        up     = array([0.0, 1.0, 0.0])
        offset = array([0.0, 0.0, 0.0])
        
        cntxt = cwv.wv_createContext(0, 30.0, 1.0, 10.0, eye, center, up)       
        
        