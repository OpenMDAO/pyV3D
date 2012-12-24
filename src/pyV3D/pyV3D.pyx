# file: pyV3D.pyx
#
# References:
#
# Tutorial for passing a numpy array into a function:
#     http://wiki.cython.org/tutorials/NumpyPointerToC
#
# Help for passing a python function into a C library
#     http://stackoverflow.com/questions/8800838/how-to-pass-a-function-pointer-to-an-external-program-in-cython?rq=1
#
# Passing string (char*) into Cython
#     http://docs.cython.org/src/tutorial/strings.html
#
# Passing string (char*) back into Python
#     http://docs.cython.org/src/tutorial/strings.html

from ctypes import addressof

cimport numpy as np

#cimport cwv

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

#ctypedef int (*callback) (void*, unsigned char*, int, void*) 
#ctypedef int (*cy_callback) (void *wsi, unsigned char *buf, int ibuf, void *f) 

cdef extern from "wv.h":

    ctypedef struct wvStripe:
        int            nsVerts
        int            nsIndices
        int            nlIndices
        int            npIndices
        int            *gIndices
        float          *vertices
        float          *normals
        unsigned char  *colors
        unsigned short *sIndice2
        unsigned short *lIndice2
        unsigned short *pIndice2

    ctypedef struct wvGPrim:
        int            gtype
        int            updateFlg
        int            nStripe
        int            attrs
        int            nVerts
        int            nIndex
        int            nlIndex
        int            npIndex
        int            nameLen
        float          pSize
        float          pColor[3]
        float          lWidth
        float          lColor[3]
        float          fColor[3]
        float          bColor[3]
        float          normal[3]
        char           *name
        float          *vertices
        float          *normals
        unsigned char  *colors
        int            *indices
        int            *lIndices
        int            *pIndices
        wvStripe       *stripes
        
    ctypedef struct wvContext:
        int     ioAccess
        int     dataAccess
        int     bias
        float   fov
        float   zNear
        float   zFar
        float   eye[3]
        float   center[3]
        float   up[3]
        int     nGPrim
        int     mGPrim
        int     cleanAll
        wvGPrim *gPrims
        
    ctypedef struct wvData:
        int    dataType
        int    dataLen
        void  *dataPtr
        float  data[3]
  
    wvContext* wv_createContext(int bias, float fov,
                                float zNear, float zFar, float *eye,
                                float *center, float *up)

    int wv_setData(int type, int len, void *data, 
                   int VBOtype, wvData *dstruct)
                   
    int wv_addGPrim(wvContext *cntxt, char *name, int gtype, int attrs, 
                    int nItems, wvData *items)
                    
    ctypedef int (*cy_callback) (void *wsi, unsigned char *buf, int ibuf, void *f) 

    void wv_sendGPrim(void *wsi, wvContext *cntxt, unsigned char *buf, int flag,
                      cy_callback callback1, void* callback2)

    void wv_removeGPrim(wvContext *cntxt, int index)
    
    
cdef int callback(void *wsi, unsigned char *buf, int ibuf, void *f):
    '''This Cython function wraps the python return function, and
    passes whatever it needs to.
    '''
    py_wsi = 0
    print "buffer", [buf[i] for i in range(0, ibuf)]
    
    cdef bytes py_buf
    py_buf = buf[:ibuf]
        
    status = (<object>f)(py_wsi, py_buf, ibuf)
    return status        
    
cdef class WV_Wrapper:

    cdef wvContext* context
    
    def __cinit__(self):
        pass
    
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
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
            
        self.context = wv_createContext(cbias, cfov, czNear, czFar, 
                                        &eye[0], &center[0], &up[0])
        
        print self.context.zFar
        print self.context.eye[0]
        
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def add_GPrim_solid(self, name, attr, offset,
                        np.ndarray[float, ndim=1, mode="c"] vertices not None,
                        np.ndarray[int, ndim=1, mode="c"] indices not None,
                        np.ndarray[unsigned char, ndim=1, mode="c"] colors not None,
                        np.ndarray[float, ndim=1, mode="c"] normals not None
                        ):
        '''Do me a VBO solid.
        '''
        cdef int ndata, error_code, nitems
        cdef wvData items[5]
        
        nitems = 4
        
        ndata = vertices.shape[0]/3
        print "Processing %d vertices." % ndata
        
        error_code = wv_setData(WV_REAL32, ndata, &vertices[0], 
                                WV_VERTICES, &items[0])
        print "Returned Status:", error_code
        
        ndata = indices.shape[0]
        print "Processing %d indices." % ndata
        
        error_code = wv_setData(WV_INT32, ndata, &indices[0], 
                                WV_INDICES, &items[1])
        print "Returned Status:", error_code
        
        ndata = colors.shape[0]/3
        print "Processing %d colors." % ndata
        
        error_code = wv_setData(WV_UINT8, ndata, &colors[0], 
                                WV_COLORS, &items[2])
        print "Returned Status:", error_code
        
        ndata = normals.shape[0]/3
        print "Processing %d normals." % ndata
        
        error_code = wv_setData(WV_REAL32, ndata, &normals[0], 
                                WV_NORMALS, &items[3])
        print "Returned Status:", error_code
        
        # Add the primary
        print "Adding the GPrim Object"
        error_code = wv_addGPrim(self.context, name, WV_TRIANGLE, attr, 
                                  nitems, items)
        print "Returned Status:", error_code
        print "GPrim %s added." % self.context.gPrims.name
        
        print "There are %d primaries in context" % self.context.nGPrim
        
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def send_GPrim(self, wsi, bytes buf, flag, wv_SendBinaryData):
        '''sends the appropriate message(s) to an individual client (browser)
        should be called by the server for every current client instance
        
        wsi: (void*)
            blind pointer that gets passed on to the send function
            
        buf: (unsigned char *)
            the allocated buffer to pack the message
            
        flag: int
             what to do:
               1 - send init message
               0 - send only gPrim updates
              -1 - send the first suite of gPrims
                
         wv_sendBinaryData(wsi, buf, len): function
             callback function to send the packets
        '''
        
        wv_sendGPrim(<void*>wsi, self.context, buf, flag, 
                     callback, <void *>wv_SendBinaryData)
                     
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def remove_GPrim(self, int index):
        '''Remove a Graphics Primary from our context.
        
        index: int
            index number for the gPrim to remove
        '''
        
        wv_removeGPrim(self.context, index)
        print "Gprim %d removed from context" % index
