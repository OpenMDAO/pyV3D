# file: pyV3D.pyx

cimport cwv
#from numpy import array
from array import array

cdef class WV_Wrapper:

    #def __init__(self):
    #    pass
        
    def __cinit__(self):
        #eye    = array([1.0, 0.0, 7.0])
        #center = array([0.0, 0.0, 0.0])
        #up     = array([0.0, 1.0, 0.0])
        #offset = array([0.0, 0.0, 0.0])
        #self._c_cntx = cwv.wv_createContext(0, 30.0, 1.0, 10.0, eye, center, up)
        pass
    
    def zzz1(self):
        return 3.14
        
    cpdef float zzz2(self):
        return 3.14
        
    cpdef wv_createContext(self, float bias, float fov, float zNear, 
                                     float zFar, float* eye, float* center, 
                                     float* up):
            
        #cwv.wv_createContext(0, 30.0, 1.0, 10.0, eye, center, up)
        pass
        
    cdef int test(self):
        '''Playing around'''

        #eye    = array([1.0, 0.0, 7.0])
        #center = array([0.0, 0.0, 0.0])
        #up     = array([0.0, 1.0, 0.0])
        #offset = array([0.0, 0.0, 0.0])
        
        #cntxt = cwv.wv_createContext(0, 30.0, 1.0, 10.0, eye, center, up)  
        
        #data = {}
        #data['dataType'] = 0
        #data['dataLen']  = 1
        #data['dataPtr'] = 0
        #data['dataPtr'] = (1,2,3)
        #status = cwv.wv_setData(0, 1, 1, 0, <void*>data);
        #return status
        
        