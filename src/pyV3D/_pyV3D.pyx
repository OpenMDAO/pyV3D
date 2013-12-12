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

from libc.stdio cimport printf, fprintf, fopen, fclose, FILE
from cpython cimport PyBytes_AsString

cimport numpy as np
import numpy as np
import struct
import os

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


cdef extern from "wv.h":

    int BUFLEN

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
    
    void wv_removeAll(wvContext *cntxt)
    
    void wv_prepareForSends(wvContext *cntxt)
    
    void wv_finishSends(wvContext *cntxt)
    
    void wv_destroyContext(wvContext **context)

    int wv_addArrowHeads(wvContext *cntxt, int index, float size, 
                         int nHeads, int *heads)

    void wv_adjustVerts(wvData *dstruct, float *focus)

    void wv_focusVertices(int nVerts, float *vertices, float *focus)

    float * wv_getBoundingBox(int nGPrims, wvGPrim * gPrims, float *bbox)

    float * wv_getFocus(float *bbox, float *focus)

    void wv_setBias(wvContext *cntxt, int bias)

    int wv_checkConnectivities(int nPoints, int nTriangles, int * pointIndices, int bias)
    

import sys


    
cdef int callback(void *wsi, unsigned char *buf, int ibuf, void *f):
    '''This Cython function wraps the python return function, and
    passes it a buffer of binary data and a pointer to the WV_Wrapper.
    '''
    cdef int status
    cdef bytes py_buf = buf[:ibuf]  #TODO: see about getting rid of this copy 

    status = (<object>f)(<object>wsi, py_buf, ibuf)
    return status     

   
cdef float* _get_focus(bbox, float focus[4]):
    import warnings
    warnings.warn("pyV3D._get_focus is deprecated", DeprecationWarning) 

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


def make_attr(visible=False,
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

class GraphicsPrimitive(object):
    def __init__(self, points=None,
                       colors=None,
                       name="",
                       bounding_box=None,
                       is_visible=True,
                       is_transparent=False,
                       has_shading=False,
                       has_orientation=True,
                       points_visible=False,
                       lines_visible=False,
                       focus=None):

        self.points=points
        self.colors=colors
        self.name=name
        self.bbox=bounding_box
        self.visible=is_visible
        self.transparency=is_transparent
        self.shading=has_shading
        self.orientation=has_orientation
        self.points_visible=points_visible
        self.lines_visible=lines_visible
        self.focus=focus

    def add_primitive_to_context(self, wv_wrapper):
        pass

class Triangle(GraphicsPrimitive):
    def __init__( self, points=None,
                        tris=None,
                        colors=None,
                        normals=None,
                        name="",
                        bbox=None,
                        visible=True,
                        transparency=False,
                        shading=False,
                        orientation=True,
                        points_visible=False,
                        lines_visible=False,
                        focus=None):
        
        super(Triangle, self).__init__(
                                        points,
                                        colors,
                                        name,
                                        bbox,
                                        visible,
                                        transparency,
                                        shading,
                                        orientation,
                                        points_visible,
                                        lines_visible,
                                        focus)
                                        
        self.tris=tris
        self.normals=normals

    def add_primitive_to_context(self, wv_wrapper):
        wv_wrapper.add_triangle(
                                self.points, self.tris, self.colors,
                                self.normals, self.name, self.bbox.flatten(),
                                self.visible, self.transparency, self.shading,
                                self.orientation, self.points_visible, self.lines_visible,
                                focus=self.focus)

class Line(GraphicsPrimitive):
    def __init__( self, points=None,
                        colors=None,
                        name="",
                        bounding_box=None,
                        is_visible=True,
                        is_transparent=False,
                        has_shading=False,
                        has_orientation=False,
                        points_visible=False,
                        lines_visible=False,
                        focus=None):

        super(Line, self).__init__(
                                    points,
                                    colors,
                                    name,
                                    bounding_box,
                                    is_visible,
                                    is_transparent,
                                    has_shading,
                                    has_orientation,
                                    points_visible,
                                    lines_visible)

    def add_primitive_to_context(self, wv_wrapper):
        wv_wrapper.add_line(
                                self.points, self.colors,
                                self.name, self.bbox.flatten(),
                                self.visible, self.transparency, self.shading,
                                self.orientation, self.points_visible, self.lines_visible,
                                self.focus)
class ConnectivitiesError(Exception):
    pass

# raise an exception for return values < 0
def _check(int ret, name='?', errclass=RuntimeError):
    if ret < 0:
        raise errclass("ERROR: return value of %d from function '%s'" % (ret, name))
    return ret
    
cdef class WV_Wrapper:

    cdef wvContext* context
    
    def __cinit__(self):
        self.context = NULL
        self.buffer = BUFLEN*b'\0'
    
    def __dealloc__(self):
        """Frees the memory for the wvContext object"""
        if self.context != NULL:
            wv_destroyContext(&self.context)
    
    def __init__(self):
        self.graphics_primitives=[]

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
        
    def get_bufflen(self):
        return BUFLEN
                
    def clear(self):
        '''Remove all GPrim data.'''
        wv_removeAll(self.context)
        self.graphics_primitives=[]

    #@cython.boundscheck(False)
    #@cython.wraparound(False)        
    def send_GPrim(self, wsi, int flag, wv_SendBinaryData):
        '''sends the appropriate message(s) to an individual client (browser)
        should be called by the server for every current client instance
        
        wsi: (void*)
            blind pointer to the webserver. This gets passed on to the 
            send function
            
        flag: int
             what to do:
               1 - send init message
               0 - send only gPrim updates
              -1 - send the first suite of gPrims
                
         wv_sendBinaryData(wsi, buf, len): function
             callback function to send the packets
        '''
        cdef unsigned char* cbuf = self.buffer
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
        self.graphics_primitives.remove(index)
         
        
    def prepare_for_sends(self):
        bounding_boxes = np.array([], dtype=np.float32)
        
        for primitive in self.graphics_primitives:
            if not primitive.bbox:
                primitive.bbox = get_bounding_box(primitive.points)
                    
            bounding_boxes = np.append(bounding_boxes, primitive.bbox)

        bounding_box = get_bounding_box(bounding_boxes.flatten())
        focus = get_focus(bounding_box.flatten())

        for primitive in self.graphics_primitives:
            primitive.bbox = bounding_box
            primitive.focus = primitive.focus

        
        for primitive in self.graphics_primitives:
            #primitive.points[::3]  = primitive.points[::3]  - x_center
            #primitive.points[1::3] = primitive.points[1::3] - y_center
            #primitive.points[2::3] = primitive.points[2::3] - z_center
            #for index in xrange(len(primitive.points)/3):
            #offset = np.tile((x_center, y_center, z_center),primitive.points.shape[0]/3)
            #primitive.points = primitive.points - offset
            #primitive.points = primitive.points/max_coordinate
            #primitive.points = adjust_points(focus, primitive.points)
                #point=primitive.points[index*3:index*3+3]
                #primitive.points[index*3:index*3+3] =  adjust_point(focus, point)

            primitive.add_primitive_to_context(self)
        #self.focus_vertices()
        '''The server needs to call this before sending GPrim info.'''

        wv_prepareForSends(self.context)
        
        
    def finish_sends(self):
        '''The server needs to call this before sending GPrim info.'''
        
        wv_finishSends(self.context)

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
                             lines_visible=False):
        
        self.graphics_primitives.append(
                            Triangle(
                                points=points,
                                tris=tris,
                                colors=colors,
                                normals=normals,
                                name=name,
                                bbox=bbox,
                                visible=visible,
                                transparency=transparency,
                                shading=shading,
                                orientation=orientation,
                                points_visible=points_visible,
                                lines_visible=lines_visible)
                        )

    def set_edge_data(self,  np.ndarray[np.float32_t, mode="c"] points not None,
                             np.ndarray[np.float32_t, mode="c"] colors=None,
                             name='',
                             bbox=None,
                             visible=True,
                             transparency=False,
                             shading=False,
                             orientation=False,
                             points_visible=False,
                             lines_visible=False):
        
        self.graphics_primitives.append(
                            Line(
                                points,
                                colors,
                                name,
                                bbox,
                                visible,
                                transparency,
                                shading,
                                orientation,
                                points_visible,
                                lines_visible)
                        )

    def add_triangle(self,  np.ndarray[np.float32_t, mode="c"] points not None,
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
                             focus=None):
        """
        Set up VBO data for a face.
        
            points: float32 Numpy ndarray (1xN*3 or Nx3)
                Vector of point coordinates for the given face.

            tris: int Numpy ndarray (1xM*3 or Mx3)
                Vector of triangle connectivities.

            colors: float32 Numpy ndarray (1x3) or (1xM*3)
                Optional. Vector of color coordinates for this group of points.  Can give a single color [r,g,b] or a color for each tri.

            normals: Numpy ndarray (1xM*3 or Mx3)
                Optional. Vector of triangle outward-pointing normals.

            name: string
                Name of graphics primitive.

            bbox: array, ndarray, or list of size 6 [xmin,ymin,zmin,xmax,ymax,zmax]
                Bounding box.
                
            visible: bool
                Set to true to make this object visible. Default=True
                
            transparency: bool
                Set to true to turn on transparency

            shading: bool
                Set to true to turn on shading

            orientation: bool
                Set to true to turn on orientation (TODO: What is this?)

            points_visible: bool
                Set to true to turn on display of vertices

            lines_visible: bool
                Set to true to turn on display of edges
        """
        cdef int attr
        cdef char *gpname
        cdef wvData items[6]
        cdef np.ndarray[np.int32_t, ndim=1, mode="c"] segs
        cdef np.ndarray[np.float32_t, ndim=1, mode="c"] color
        cdef int bias

        bias = self.context.bias
        

        attr = make_attr(visible=visible, 
                         transparency=transparency, 
                         shading=shading, 
                         orientation=orientation,
                         points_visible=points_visible, 
                         lines_visible=lines_visible)

        ntris = len(tris)/3
        num_points = len(points)/3

        #Check that triangles use valid point indices
        _check(
            wv_checkConnectivities(num_points, ntris, &tris[0], bias),
            name="wv_checkConnectivities",
            errclass=ConnectivitiesError
            )

        if focus != None:
            points = adjust_points(focus, points)
            
        elif bbox != None:
            points = adjust_points(get_focus(bbox), points)

        # vertices 
        _check(wv_setData(WV_REAL32, len(points)/3, &points[0], WV_VERTICES, &items[0]),
               "wv_setData")

        # triangles
        _check(wv_setData(WV_INT32, 3*ntris, &tris[0], WV_INDICES, &items[1]),
               "wv_setData")

        # triangle colors
        if colors is None:
            colors = np.array([1.0, 0.0, 0.0], dtype=np.float32, order='C')

        _check(wv_setData(WV_REAL32, len(colors)/3, &colors[0], WV_COLORS, &items[2]), "wv_setData")

        # normals
        if normals is not None:
            _check(wv_setData(WV_REAL32, len(points)/3, &normals[0], WV_NORMALS, &items[3]),
                   "wv_setData")
            it_col = 4
        else:
            it_col = 3
            

        # triangle sides (segments)
        segs = np.empty(6*ntris, dtype=np.int32, order='C')
        nseg = 0
        for itri in range(ntris):
            for k in range(3):
                segs[2*nseg] = tris[3*itri+(k+1)%3]
                segs[2*nseg+1] = tris[3*itri+(k+2)%3]
                nseg+=1

        _check(wv_setData(WV_INT32, 2*nseg, &segs[0], WV_LINDICES, &items[it_col]),
            "wv_setData")

        # segment colors
        color = np.array([0.0, 0.0, 0.0], dtype=np.float32, order='C')

        _check(wv_setData(WV_REAL32, 1, &color[0], WV_LCOLOR, &items[it_col+1]), "wv_setData")

        # make graphic primitive 
        gpname = name
        igprim = _check(wv_addGPrim(self.context, gpname, WV_TRIANGLE, attr, 5, items),
            "wv_addGPrim")
        # make line width 1 
        if self.context.gPrims != NULL:
            self.context.gPrims[igprim].lWidth = 1.0


    def add_line(self,  
                      np.ndarray[np.float32_t, mode="c"] points not None,
                      np.ndarray[np.float32_t, mode="c"] colors=None,
                      name='',
                      bbox=None,
                      visible=True,
                      transparency=False,
                      shading=False,
                      orientation=False,
                      points_visible=False,
                      lines_visible=False,
                      focus=None):
        """
        Set up VBO data for an edge.

            points: float32 Numpy ndarray (1xN*3 or Nx3)
                Vector of point coordinates for the given edge.
            
            colors: float32 Numpy ndarray (1x3) or 1xN*3
                Optional. Vector of color coordinates for this group of points.

            bbox: array, ndarray, or list of size 6 [xmin,ymin,zmin,xmax,ymax,zmax]
                Bounding box.
                
            visible: bool
                Set to true to make this object visible. Default=True
                
            visible: bool
                Set to true to make this object visible. Default=True
                
            transparency: bool
                Set to true to turn on transparency

            shading: bool
                Set to true to turn on shading

            orientation: bool
                Set to true to turn on orientation (TODO: What is this?)

            points_visible: bool
                Set to true to turn on display of vertices

            lines_visible: bool
                Set to true to turn on display of edges
       """
        cdef char *gpname
        cdef int head, attr
        cdef wvData items[5]
        cdef np.ndarray[np.float32_t, ndim=1, mode="c"] xyzs

        npts = len(points)/3
        head = npts - 1

        attr = make_attr(visible=visible, 
                         transparency=transparency, 
                         shading=shading, 
                         orientation=orientation,
                         points_visible=points_visible, 
                         lines_visible=lines_visible)

        xyzs = np.empty(6*head, dtype=np.float32, order='C')

        for nseg in range(head):
            xyzs[6*nseg  ] = points[3*nseg  ]
            xyzs[6*nseg+1] = points[3*nseg+1]
            xyzs[6*nseg+2] = points[3*nseg+2]
            xyzs[6*nseg+3] = points[3*nseg+3]
            xyzs[6*nseg+4] = points[3*nseg+4]
            xyzs[6*nseg+5] = points[3*nseg+5]

        if focus != None:
            points = adjust_points(focus, points)
            
        elif bbox != None:
            points = adjust_points(get_focus(bbox), points)

        # vertices 
        _check(wv_setData(WV_REAL32, 2*head, &xyzs[0], WV_VERTICES, &items[0]),
            "wv_setData")
 
        # line colors
        if colors is None:
            colors = np.array([0.0, 0.0, 1.0], dtype=np.float32, order='C')

        _check(wv_setData(WV_REAL32, len(colors)/3, &colors[0], WV_COLORS, &items[1]),
            "wv_setData")

        gpname = name

        # make graphic primitive 
        igprim = _check(wv_addGPrim(self.context, gpname, WV_LINE, attr, 2, items),
            "wv_addGPrim")
        # make line width 1.5 
        if self.context.gPrims != NULL:
            self.context.gPrims[igprim].lWidth = 1.5

        # this core dumps on windows and doesn't work properly elsewhere, so
        # leave it out for now
        #if head != 0:
        #    wv_addArrowHeads(self.context, igprim, 0.05, 1, &head)
     
    def focus_vertices(self):
        import warnings
        warnings.warn("pyV3D.focus_vertices is deprecated", DeprecationWarning)
        cdef float boundingBox[6]
        cdef float focus[4]
        cdef float * vertices
        cdef int nGPrim, nVerts
        cdef wvGPrim * gPrim
         
        nGPrim = self.context.nGPrim
        gPrim = self.context.gPrims

        wv_getBoundingBox(nGPrim, &gPrim[0], &boundingBox[0])
        wv_getFocus(&boundingBox[0], &focus[0])
       
        for i in range(nGPrim):
            nVerts = gPrim[i].nVerts
            vertices = gPrim[i].vertices

            wv_focusVertices(nVerts, &vertices[0], &focus[0])

    def set_context_bias(self, int bias):
        cdef wvContext * context
        
        context = self.context
        wv_setBias(&context[0], bias)


def get_bounding_box(points):
    x_min = x_max = points[0]
    y_min = y_max = points[1]
    z_min = z_max = points[2]


    for index in xrange(points.shape[0]/3):
        x = points[index*3]
        y = points[index*3+1]
        z = points[index*3+2]

        x_min = min(x, x_min)
        y_min = min(y, y_min)
        z_min = min(z, z_min)
       
        x_max = max(x, x_max)
        y_max = max(y, y_max)
        z_max = max(z, z_max)

    return np.array([[x_max, y_max, z_max], [x_min, y_min, z_min]],dtype=np.float32)

def get_focus(bounding_box):
    x_max = bounding_box[0]
    y_max = bounding_box[1]
    z_max = bounding_box[2]

    x_min = bounding_box[3]
    y_min = bounding_box[4]
    z_min = bounding_box[5]

    x_center = 0.5*(x_max + x_min)
    y_center = 0.5*(y_max + y_min)
    z_center = 0.5*(z_max + z_min)

    max_coordinate_magnitude = abs(x_max - x_center)
    max_coordinate_magnitude = max(abs(y_max - y_center), max_coordinate_magnitude)
    max_coordinate_magnitude = max(abs(z_max - z_center), max_coordinate_magnitude)

    return np.array([x_center, y_center, z_center, max_coordinate_magnitude], dtype=np.float32)
     
def adjust_points(focus, points):
    x_center, y_center, z_center, max_coordinate = focus
    offset = np.tile((x_center, y_center, z_center),points.shape[0]/3)
    points = points - offset
    points = points/max_coordinate

    return points
