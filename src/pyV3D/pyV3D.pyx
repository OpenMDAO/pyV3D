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
import numpy as np

# Attributes.
WV_ON          =  1
WV_TRANSPARENT =  2
WV_SHADING     =  4
WV_ORIENTATION =  8
WV_POINTS      = 16
WV_LINES       = 32

# VBOtypes.
WV_VERTICES =   1
WV_INDICES  =   2
WV_COLORS   =   4
WV_NORMALS  =   8
WV_PINDICES =  16
WV_LINDICES =  32
WV_PCOLOR   =  64
WV_LCOLOR   = 128
WV_BCOLOR   = 256

# GPTypes.
WV_POINT    = 0
WV_LINE     = 1
WV_TRIANGLE = 2

# Data types
WV_UINT8  = 1
WV_UINT16 = 2
WV_INT32  = 3
WV_REAL32 = 4
WV_REAL64 = 5

# Type dictionary
#TYPE_DICT = { 'uint8'   : WV_UINT8,
#              'uint16'  : WV_UINT16,
#              'int32'   : WV_INT32,
#              'float32' : WV_REAL32,
#              'float64' : WV_REAL64 }

from libc.stdio cimport printf

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
                    
    void wv_printGPrim(wvContext *cntxt, int index)

    int wv_indexGPrim(wvContext *cntxt, char *name)

    ctypedef int (*cy_callback) (void *wsi, unsigned char *buf,
                                 int ibuf, void *f) 

    int wv_sendGPrim(void *wsi, wvContext *cntxt, unsigned char *buf, int flag,
                      cy_callback callback1, void* callback2)

    void wv_removeGPrim(wvContext *cntxt, int index)
    
    void wv_prepareForSends(wvContext *cntxt)
    
    void wv_finishSends(wvContext *cntxt)
    
    void wv_destroyContext(wvContext **context)

    int wv_addArrowHeads(wvContext *cntxt, int index, float size, 
                         int nHeads, int *heads)

    void wv_adjustVerts(wvData *dstruct, float *focus)

    void wv_createBox(wvContext *cntxt, char *name, int attr, float *offset)
    


import sys

def dbg(*args):
    for msg in args:
        sys.stderr.write(str(msg))
        sys.stderr.write(" ")
    sys.stderr.write("\n")
    
    
cdef int callback(void *wsi, unsigned char *buf, int ibuf, void *f):
    '''This Cython function wraps the python return function, and
    passes it a buffer of binary data and a pointer to the web server.
    '''
    cdef bytes py_buf
    py_buf = buf[:ibuf]
        
    status = (<object>f)(<object>wsi, py_buf, ibuf)
    return status     
    
cdef float* _get_focus(bbox):
    cdef float focus[4]
    
    size = bbox[3] - bbox[0]
    if (size < bbox[4]-bbox[1]):
        size = bbox[4] - bbox[1]
    if (size < bbox[5]-bbox[2]):
        size = bbox[5] - bbox[2]

    focus[0] = 0.5*(bbox[0] + bbox[3])
    focus[1] = 0.5*(bbox[1] + bbox[4])
    focus[2] = 0.5*(bbox[2] + bbox[5])
    focus[3] = size

    return focus


cdef int make_attr(visible=True,
                   transparency=False,
                   shading=False,
                   orientation=False,
                   points_visible=False,
                   lines_visible=False):
        # Assemble the attributes
    cdef int attr=0

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

    return attr

# raise an exception for return values < 0
def _check(int ret, name='?', errclass=RuntimeError):
    if ret < 0:
        raise errclass("ERROR: return value of %d from function '%s'" % (ret, name))
    return ret

cdef class WV_Wrapper:

    cdef wvContext* context
    
    def __cinit__(self):
        pass
    
    def __dealloc__(self):
        """Frees the memory for the wvContext object"""
        
        wv_destroyContext(&self.context)
        print "Context cleaned up."
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def createContext(self, bias, fov, zNear, zFar, 
                      np.ndarray[np.float32_t, ndim=1, mode="c"] eye not None,
                      np.ndarray[np.float32_t, ndim=1, mode="c"] center not None,
                      np.ndarray[np.float32_t, ndim=1, mode="c"] up not None
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
        
        
    def load_geometry(self, geometry, sub_index=None, name='geometry',
                      angle=0., relSide=0., relSag=0.):
        '''Load a tesselation from a geometry model.
        
        geometry: GEMGeometry
            A geometry object that adheres to the IGeometry interface
            
        sub_index: int
            An index into the geometry object that designates a
            submodel to be visualized. If not supplied, the whole model
            will be visualized.
        '''
        geometry.get_visualization_data(self, sub_index,
              angle=angle, relSide=relSide, relSag=relSag)
        # data = geometry.return_visualization_data(sub_index)
        
        # indices = []
        # for i, tesselation in enumerate(data):
        
        #     idx = self.add_GPrim_solid(name+"_%d" % i, 
        #                                tesselation[0], tesselation[1],
        #                                shading=True, orientation=True)
        #     if idx < 0:
        #         raise RuntimeError("failed to add GPrim_solid %s" % name)
                
        #     indices.append(idx)
            
        # return indices        
        
    def load_DRep(self, drep, ibrep, nfaces, name=None):
        '''Load model ibrep from a GEM DRep
        
        TODO: This method is deprecated.'''
        
        indices = []
        for iface in range(1, nfaces+1):
            triArray, xyzArray = drep.getTessel(ibrep, iface)
            
            # Flatten here until I can figure out why they aren't
            # flattening in add_GPrim_*
            triArray = triArray.astype(np.int32).flatten()
            xyzArray = xyzArray.astype(np.float32).flatten()
            
            idx = self.add_GPrim_solid(name+"_face%d" % iface, xyzArray, triArray,
                                       shading=True, orientation=True)
            if idx < 0:
                raise RuntimeError("failed to add GPrim_solid %s" % name)
            indices.append(idx)
        return indices
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def add_GPrim_solid(self, name, 
                        np.ndarray[np.float32_t, mode="c"] vertices not None,
                        np.ndarray[int, mode="c"] indices not None,
                        np.ndarray[unsigned char, mode="c"] colors=None,
                        np.ndarray[np.float32_t, mode="c"] normals=None,
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
        
        cdef int i, ndata, error_code, nitems, attr, ret
        cdef wvData items[5]
        cdef char *cname
        
        nitems = 2
        
        ndata = vertices.shape[0]/3
        dbg("Processing %d vertices." % ndata)
        
        error_code = wv_setData(WV_REAL32, ndata, &vertices[0], 
                                WV_VERTICES, &items[0])
        dbg("Returned Status:", error_code)
        if error_code != 0:
            return error_code
        
        ndata = indices.shape[0]
        dbg("Processing %d indices." % ndata)
        
        error_code = wv_setData(WV_INT32, ndata, &indices[0], 
                                WV_INDICES, &items[1])
        dbg("Returned Status: %s" % error_code)
        if error_code != 0:
            return error_code
        
        if colors is not None:
            ndata = colors.shape[0]/3
            dbg("Processing %d colors." % ndata)
        
            error_code = wv_setData(WV_UINT8, ndata, &colors[0], 
                                    WV_COLORS, &items[nitems])
            dbg("Returned Status:", error_code)
            if error_code != 0:
                return error_code
            nitems += 1
        
        if normals is not None:
            ndata = normals.shape[0]/3
            dbg("Processing %d normals." % ndata)
        
            error_code = wv_setData(WV_REAL32, ndata, &normals[0], 
                                    WV_NORMALS, &items[nitems])
            dbg("Returned Status:", error_code)
            if error_code != 0:
                return error_code
            nitems += 1
        
        attr = make_attr(visible, transparency, shading, orientation,
                         points_visible, lines_visible)

        dbg("attr=",attr)
        
        # Add the primitive
        dbg("Adding the GPrim Object. nitems=%d, name=%s" %(nitems, name))
        cname = name
        ret = wv_addGPrim(self.context, cname, WV_TRIANGLE, attr, 
                                  nitems, items)
        dbg("done adding GPrim")
        if ret < 0:
            dbg("Returned error code:", ret)
        else:
            dbg("Returned Gprim index:", ret)
        dbg("GPrim %s added." % self.context.gPrims.name)
        
        dbg("There are %d primitives in context" % self.context.nGPrim)

        #wv_printGPrim(self.context, wv_indexGPrim(self.context, cname))

        return ret
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def add_GPrim_wireframe(self, name,
                            np.ndarray[np.float32_t, mode="c"] vertices not None,
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

        cdef int ndata, error_code, nitems, ret
        cdef wvData items[2]
        nitems = 2
        
        ndata = vertices.shape[0]/3
        dbg("Processing %d vertices." % ndata)
        
        error_code = wv_setData(WV_REAL32, ndata, &vertices[0], 
                                WV_VERTICES, &items[0])
        dbg("Returned Status:", error_code)
        if error_code != 0:
            return error_code
        
        ndata = indices.shape[0]
        dbg("Processing %d indices." % ndata)
        
        error_code = wv_setData(WV_INT32, ndata, &indices[0], 
                                WV_INDICES, &items[1])
        dbg("Returned Status:", error_code)
        if error_code != 0:
            return error_code

        # Assemble the attributes
        attr = 0
        if visible:
            attr = attr|WV_ON
        
        # Add the primitive
        dbg("Adding the GPrim Object")
        ret = wv_addGPrim(self.context, name, WV_LINE, attr, 
                          nitems, items)
        if ret < 0:
            dbg("Returned error code:", ret)
        else:
            dbg("Returned Gprim index:", ret)
        dbg("GPrim %s added." % self.context.gPrims.name)
        
        dbg("There are %d primitives in context" % self.context.nGPrim)

        return ret
        

    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def add_GPrim_pointcloud(self, name,
                             np.ndarray[np.float32_t, mode="c"] vertices not None,
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

        cdef int ndata, error_code, nitems, ret
        cdef wvData items[2]
        nitems = 1
        
        ndata = vertices.shape[0]/3
        print "Processing %d vertices." % ndata
        
        error_code = wv_setData(WV_REAL32, ndata, &vertices[0], 
                                WV_VERTICES, &items[0])
        print "Returned Status:", error_code
        if error_code != 0:
            return error_code
        
        if colors is not None:
            ndata = 1
            print "Processing %d colors." % ndata
        
            error_code = wv_setData(WV_REAL32, ndata, &colors[0], 
                                    WV_COLORS, &items[nitems])
            print "Returned Status:", error_code
            if error_code != 0:
                return error_code
            nitems += 1
        
        # Assemble the attributes
        attr = 0
        if visible:
            attr = attr|WV_ON
        
        # Add the primitive
        print "Adding the GPrim Object"
        ret = wv_addGPrim(self.context, name, WV_POINT, attr, 
                                  nitems, items)
        if ret < 0:
            print "Returned error code:", ret
        else:
            print "Returned Gprim index:", ret
        print "GPrim %s added." % self.context.gPrims.name
        
        print "There are %d primitives in context" % self.context.nGPrim

        return ret
        
        
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def send_GPrim(self, wsi, bytes buf, int flag, wv_SendBinaryData):
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
        cdef unsigned char* cbuf = buf
        _check(wv_sendGPrim(<void*>wsi, self.context, cbuf, flag, 
                     callback, <void *>wv_SendBinaryData), "wv_sendGPrim")
                     
    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def remove_GPrim(self, int index):
        '''Remove a Graphics Primary from our context.
        
        index: int
            index number for the gPrim to remove
        '''
        
        wv_removeGPrim(self.context, index)
        dbg("Gprim %d removed from context" % index)
        
        
    def prepare_for_sends(self):
        '''The server needs to call this before sending GPrim info.'''

        wv_prepareForSends(self.context)
        
        
    def finish_sends(self):
        '''The server needs to call this before sending GPrim info.'''
        
        wv_finishSends(self.context)


    def createBox(self, char *name, int flag, offset):
        cdef float coffset[3]
        for i in range(3):
            coffset[i] = offset[i]
        wv_createBox(self.context, name, flag, coffset)


    def set_face_data(self,  np.ndarray[np.float32_t, mode="c"] points not None,
                             np.ndarray[int, mode="c"] tris not None,
                             np.ndarray[np.float32_t, mode="c"] colors=None,
                             np.ndarray[np.float32_t, mode="c"] normals=None,
                             name='',
                             bbox=None,
                             visible=True,
                             transparency=False,
                             shading=False,
                             orientation=True,
                             points_visible=False,
                             lines_visible=False,

                             fp=None):
        cdef int attr
        cdef float color[3], focus[4]
        cdef char *gpname
        cdef wvData items[5]
        cdef np.ndarray[np.int32_t, ndim=1, mode="c"] segs

        attr = make_attr(visible, transparency, shading, orientation,
                         points_visible, lines_visible)

        ntris = len(tris)/3
        fp.write("npts, ntris = %d, %d\n" % (len(points)/3, ntris))
        # vertices 
        fp.write("vertices:\n")
        for jj in range (len(points)/3):
            fp.write("%f, %f, %f\n" % (points[jj*3],points[1+jj*3],points[2+jj*3]))

        _check(wv_setData(WV_REAL64, len(points)/3, &points[0], WV_VERTICES, &items[0]),
               "wv_setData")
        if bbox:
            wv_adjustVerts(&items[0], _get_focus(bbox))

        # triangles
        fp.write("triangles:\n")
        for jj in range(ntris):
            fp.write("%d, %d, %d\n" % (tris[jj*3],tris[1+jj*3],tris[2+jj*3]))
        _check(wv_setData(WV_INT32, 3*ntris, &tris[0], WV_INDICES, &items[1]),
               "wv_setData")

        # triangle colors
        if colors is None:
            color[0] = 1.0
            color[1] = 0.0
            color[2] = 0.0
        else:
            color[0] = colors[0]
            color[1] = colors[1]
            color[2] = colors[2]

        fp.write("colors: %f, %f, %f\n" % (color[0],color[1],color[2]))
        _check(wv_setData(WV_REAL32, 1, color, WV_COLORS, &items[2]), "wv_setData")

        # triangle sides (segments)
        segs = np.empty(6*ntris, dtype=np.int32, order='C')
        nseg = 0
        for itri in range(ntris):
            for k in range(3):
                segs[2*nseg] = tris[3*itri+(k+1)%3]
                segs[2*nseg+1] = tris[3*itri+(k+2)%3]
                nseg+=1

        fp.write("nseg=%d\nsegs:\n" % nseg)
        for jj in range(2*nseg):
            fp.write("%d\n" % segs[jj])
        _check(wv_setData(WV_INT32, 2*nseg, &segs[0], WV_LINDICES, &items[3]),
            "wv_setData")

        # segment colors
        color[0] = 0.0;
        color[1] = 0.0;
        color[2] = 0.0;

        fp.write("seg colors: %f, %f, %f\n" % (color[0],color[1],color[2]))
        _check(wv_setData(WV_REAL32, 1, color, WV_LCOLOR, &items[4]), "wv_setData")

        # make graphic primitive 
        gpname = name
        fp.write("adding GPRim, attr=%d, nitems=%d\n"% (attr, 5))
        igprim = _check(wv_addGPrim(self.context, gpname, WV_TRIANGLE, attr, 5, items),
            "wv_addGPrim")
        # make line width 1 
        if self.context.gPrims != NULL:
            self.context.gPrims[igprim].lWidth = 1.0


    def set_edge_data(self,  np.ndarray[np.float32_t, mode="c"] points not None,
                             np.ndarray[np.float32_t, mode="c"] colors=None,
                             name='',
                             bbox=None,
                             visible=True,
                             transparency=False,
                             shading=False,
                             orientation=False,
                             points_visible=False,
                             lines_visible=False,

                             fp=None):

        cdef float color[3], focus[4]
        cdef char *gpname
        cdef int head, attr
        cdef wvData items[5]
        cdef np.ndarray[np.float32_t, ndim=1, mode="c"] xyzs

        npts = len(points)/3
        head = npts - 1

        attr = make_attr(visible, transparency, shading, orientation,
                         points_visible, lines_visible)

        xyzs = np.empty(6*head, dtype=np.float32, order='C')

        fp.write("npts=%d\nedge points:\n" % npts)
        for nseg in range(head):
            xyzs[6*nseg  ] = points[3*nseg  ]
            xyzs[6*nseg+1] = points[3*nseg+1]
            xyzs[6*nseg+2] = points[3*nseg+2]
            xyzs[6*nseg+3] = points[3*nseg+3]
            xyzs[6*nseg+4] = points[3*nseg+4]
            xyzs[6*nseg+5] = points[3*nseg+5]
            fp.write("%f, %f, %f, %f, %f, %f\n" %(
                xyzs[6*nseg  ],
                xyzs[6*nseg+1],
                xyzs[6*nseg+2],
                xyzs[6*nseg+3],
                xyzs[6*nseg+4],
                xyzs[6*nseg+5]
                ))

        # vertices 
        _check(wv_setData(WV_REAL32, 2*head, &xyzs[0], WV_VERTICES, &items[0]),
            "wv_setData")
        if bbox:
            wv_adjustVerts(&items[0], _get_focus(bbox))
 
        # line colors
        if colors is None:
            color[0] = 0.0
            color[1] = 0.0
            color[2] = 1.0
        else:
            color[0] = colors[0]
            color[1] = colors[1]
            color[2] = colors[2]

        fp.write("edge colors: %f, %f, %f\n" % (color[0],color[1],color[2]))
        _check(wv_setData(WV_REAL32, 1, color, WV_COLORS, &items[1]),
            "wv_setData")

        gpname = name

        # make graphic primitive 
        fp.write("adding GPRim, attr=%d, nitems=%d\n" %(attr, 2))
        igprim = _check(wv_addGPrim(self.context, gpname, WV_LINE, attr, 2, items),
            "wv_addGPrim")
        # make line width 1.5 
        if self.context.gPrims != NULL:
            self.context.gPrims[igprim].lWidth = 1.5
        if head != 0:
            wv_addArrowHeads(self.context, igprim, 0.05, 1, &head)

