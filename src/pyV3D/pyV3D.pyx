# file: pyV3D.pyx
#
# References:
#
# Tutorial for passing a numpy array into a function:
#     http://wiki.cython.org/tutorials/NumpyPointerToC

from array import array

import cython
import numpy as np
cimport numpy as np

cimport cwv

# Attributes.
WV_ON = 1
WV_TRANSPARENT = 2
WV_SHADING = 4
WV_ORIENTATION = 8
WV_POINTS = 16
WV_LINES = 32

# VBOtypes.
WV_VERTICES = 1
WV_INDICES = 2
WV_COLORS = 4
WV_NORMALS = 8
WV_PINDICES = 16
WV_LINDICES = 32
WV_PCOLOR = 999 # ?
WV_LCOLOR = 888 # ?
WV_BCOLOR = 777 # ?

# GPTypes.
WV_POINT = 0
WV_LINE = 1
WV_TRIANGLE = 2

# Data types
WV_UINT8 = 1
WV_UINT16 = 2
WV_INT32 = 3
WV_REAL32 = 4
WV_REAL64 = 5

cdef class WV_Wrapper:

    cdef cwv.wvContext* context
    
    def __cinit__(self):
        pass
    
    @cython.boundscheck(False)
    @cython.wraparound(False)        
    def createContext(self, bias, fov, zNear, zFar, 
                      np.ndarray[float, ndim=1, mode="c"] eye not None,
                      np.ndarray[float, ndim=1, mode="c"] center not None,
                      np.ndarray[float, ndim=1, mode="c"] up not None
                      ):
        '''Creates the initial context for viewing the model.
        
        bias: int
            bias?
            
        fov: float
            field of view angle
            
        zNear: float
            Z value for near clipping plane
            
        zFar: float
            Z value for far clipping plane
            
        eye: numpy.array(dtype=float32, shape=(3,))
            Eye location in 3-space
            
        center: numpy.array(dtype=float32, shape=(3,))
            Location of scene center in 3-space
            
        up: numpy.array(dtype=float32, shape=(3,))
            Vector defining the up direction
        '''
                         
        cdef int cbias
        cdef float cfov, czNear, czFar
        
        cbias = bias
        cfov = fov
        czNear = zNear
        czFar = zFar
            
        self.context = cwv.wv_createContext(cbias, cfov, czNear, czFar, 
                                       &eye[0], &center[0], &up[0])
        
        print self.context.zFar
        print self.context.eye[0]
        
        
    @cython.boundscheck(False)
    @cython.wraparound(False)        
    def setdata_vertices(self,
                         np.ndarray[float, ndim=1, mode="c"] data not None,
                         ):
        '''Define the vertices for facets in a VBO.
        '''
        
        cdef int ndata, error_code
        cdef cwv.wvData items[2]
        
        ndata = data.shape[0]/3
        print "Processing %d vertices." % ndata
        
        error_code = cwv.wv_setData(WV_REAL32, ndata, &data[0], 
                                    WV_VERTICES, items)
                                    
        return error_code
        
    @cython.boundscheck(False)
    @cython.wraparound(False)        
    def setdata_normals(self,
                       np.ndarray[float, ndim=1, mode="c"] data not None,
                       ):
        '''Define the outward pointing normals for facets in a VBO.
        '''
        
        cdef int ndata, error_code
        cdef cwv.wvData items[5]
        
        ndata = data.shape[0]/3
        print "Processing %d vertices." % ndata
        
        error_code = cwv.wv_setData(WV_REAL32, ndata, &data[0], 
                                    WV_VERTICES, items)
                                    
        return error_code        