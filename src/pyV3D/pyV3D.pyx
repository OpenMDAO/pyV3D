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
#
# Passing Python objects in and out of the C code
#     http://www.cython.org/release/Cython-0.12/Cython/Includes/python.pxd

cimport numpy as np

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
                    
    ctypedef int (*cy_callback) (void *wsi, unsigned char *buf,
                                 int ibuf, void *f) 

    void wv_sendGPrim(void *wsi, wvContext *cntxt, unsigned char *buf, int flag,
                      cy_callback callback1, void* callback2)

    void wv_removeGPrim(wvContext *cntxt, int index)
    
    
cdef int callback(void *wsi, unsigned char *buf, int ibuf, void *f):
    '''This Cython function wraps the python return function, and
    passes it a buffer of binary data and a pointer to the web server.
    '''
    cdef bytes py_buf
    py_buf = buf[:ibuf]
        
    status = (<object>f)(<object>wsi, py_buf, ibuf)
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
    def add_GPrim_solid(self, name, 
                        np.ndarray[float, mode="c"] vertices not None,
                        np.ndarray[int, mode="c"] indices not None,
                        np.ndarray[unsigned char, mode="c"] colors=None,
                        np.ndarray[float, mode="c"] normals=None,
                        visible=True,
                        transparency=False,
                        shading=False,
                        orientation=False,
                        points_visible=False,
                        lines_visible=False
                        ):
        '''Do me a VBO solid.
        
        name: str
            Name of the primitive.
            
        vertices: Numpy ndarray (1xN*3 or Nx3)
            Vector of triangle vertices.
        
        indices: Numpy ndarray (1xM*3 or Mx3)
            Vector of triangle connectivities.
        
        colors: Numpy ndarray (1xM*3 or Mx3)
            Optional. Vector of color coordinates per triangle.
        
        normals: Numpy ndarray (1xM*3 or Mx3)
            Optional. Vector of triangle outward-pointing normals.
            
        visible: bool
            Set to true to make this object visible. Default=True
            
        transparency: bool
            Set to true to turn on transparency

        shading: bool
            Set to true to turn on shading

        orientation: bool
            Set to true to turn on orientation (TODO: What is this?)

        points_display: bool
            Set to true to turn on display of vertices

        lines_display: bool
            Set to true to turn on display of edges
        '''
        
        cdef int ndata, error_code, nitems
        cdef wvData items[5]
        
        nitems = 2
        
        # Check shapes
        if vertices.ndim > 1:
            vertices.flatten()
        if indices.ndim > 1:
            indices.flatten()
        
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
        
        if colors is not None:
            if colors.ndim > 1:
                colors.flatten()
            ndata = colors.shape[0]/3
            print "Processing %d colors." % ndata
        
            error_code = wv_setData(WV_UINT8, ndata, &colors[0], 
                                    WV_COLORS, &items[nitems])
            print "Returned Status:", error_code
            nitems += 1
        
        if normals is not None:
            if normals.ndim > 1:
                normals.flatten()
            ndata = normals.shape[0]/3
            print "Processing %d normals." % ndata
        
            error_code = wv_setData(WV_REAL32, ndata, &normals[0], 
                                    WV_NORMALS, &items[nitems])
            print "Returned Status:", error_code
            nitems += 1
        
        # Assemble the attributes
        attr = 0
        if visible:
            attr = attr|WV_ON
        if transparency:
            attr = attr|WV_TRANSPARENT
        if shading:
            attr = attr|WV_SHADING
        if orientation:
            attr = attr|WV_ORIENTATION
        if points_visible:
            attr = attr|WV_POINTS
        if lines_visible:
            attr = attr|WV_LINES
        
        # Add the primitive
        print "Adding the GPrim Object"
        error_code = wv_addGPrim(self.context, name, WV_TRIANGLE, attr, 
                                  nitems, items)
        print "Returned Status:", error_code
        print "GPrim %s added." % self.context.gPrims.name
        
        print "There are %d primitives in context" % self.context.nGPrim
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def add_GPrim_wireframe(self, name,
                            np.ndarray[float, mode="c"] vertices not None,
                            np.ndarray[int, mode="c"] indices not None,
                            visible=True,
                            ):
        '''Declare a wireframe VBO.
        
        name: str
            Name of the primitive.
            
        vertices: Numpy ndarray (1xN*3 or Nx3)
            Vector of vertex coordinates.
        
        indices: Numpy ndarray (1xM*2 or Mx2)
            Vector of line connectivities.
        
        visible: bool
            Set to true to make this object visible. Default=True
        '''

        cdef int ndata, error_code, nitems
        cdef wvData items[2]
        nitems = 2
        
        # Check shapes
        if vertices.ndim > 1:
            vertices.flatten()
        if indices.ndim > 1:
            indices.flatten()
        
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

        # Assemble the attributes
        attr = 0
        if visible:
            attr = attr|WV_ON
        
        # Add the primitive
        print "Adding the GPrim Object"
        error_code = wv_addGPrim(self.context, name, WV_LINE, attr, 
                                  nitems, items)
        print "Returned Status:", error_code
        print "GPrim %s added." % self.context.gPrims.name
        
        print "There are %d primitives in context" % self.context.nGPrim
        

    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def add_GPrim_pointcloud(self, name,
                             np.ndarray[float, mode="c"] vertices not None,
                             np.ndarray[unsigned char, mode="c"] colors=None,
                             visible=True,
                             ):
        '''Declare a cloud of points VBO.
        
        name: str
            Name of the primitive.
            
        vertices: Numpy ndarray (1xN*3 or Nx3)
            Vector of point coordinates.
        
        colors: Numpy ndarray (1x3)
            Optional. Vector of color coordinates for this group of points.
            
        visible: bool
            Set to true to make this object visible. Default=True
        '''

        cdef int ndata, error_code, nitems
        cdef wvData items[2]
        nitems = 1
        
        # Check shapes
        if vertices.ndim > 1:
            vertices.flatten()
        
        ndata = vertices.shape[0]/3
        print "Processing %d vertices." % ndata
        
        error_code = wv_setData(WV_REAL32, ndata, &vertices[0], 
                                WV_VERTICES, &items[0])
        print "Returned Status:", error_code
        
        if colors is not None:
            if colors.ndim > 1:
                colors.flatten()
            ndata = 1
            print "Processing %d colors." % ndata
        
            error_code = wv_setData(WV_REAL32, ndata, &colors[0], 
                                    WV_COLORS, &items[nitems])
            print "Returned Status:", error_code
            nitems += 1
        
        # Assemble the attributes
        attr = 0
        if visible:
            attr = attr|WV_ON
        
        # Add the primitive
        print "Adding the GPrim Object"
        error_code = wv_addGPrim(self.context, name, WV_POINT, attr, 
                                  nitems, items)
        print "Returned Status:", error_code
        print "GPrim %s added." % self.context.gPrims.name
        
        print "There are %d primitives in context" % self.context.nGPrim
        
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def send_GPrim(self, wsi, bytes buf, flag, wv_SendBinaryData):
        '''sends the appropriate message(s) to an individual client (browser)
        should be called by the server for every current client instance
        
        wsi: (void*)
            blind pointer to the webserver. This gets passed on to the 
            send function
            
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
