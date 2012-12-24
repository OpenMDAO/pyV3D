#
#   Cython wrapper for the cheesefinder API
#

cdef extern from "cheesefinder.h":
    ctypedef int (*cheesefunc)(char *name, void *user_data)
    void find_cheeses(void *user_data, cheesefunc user_func)

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
  
    ctypedef int (*cy_callback) (void *wsi, bytes buf, int ibuf, void *f) 

    void wv_sendGPrim(void *wsi, wvContext *cntxt, unsigned char *buf, int flag,
                      cy_callback callback1, void* callback2)
    void wv_sendGPrim2(void* callback2, cy_callback callback1)
    void wv_sendGPrim3(void* callback2, cheesefunc callback1)


cdef int callback(void *wsi, bytes buf, int ibuf, void *f):
    '''This Cython function wraps the python return function, and
    passes whatever it needs to.
    '''
    py_wsi = 0
    status = (<object>f)(py_wsi, buf, ibuf)
    return status        
    
cdef int callback2(char *name, void *f):
    z = (<object>f)(name)
    print "This is", z, type(z)
    return z

def find(f):

    find_cheeses(<void*>f, callback2)
    
    cdef wvContext* context
    wsi = 0
    buf = 24*' '
    flag = 0
    wv_sendGPrim3(<void*>f, callback2)
    wv_sendGPrim2(<void*>f, callback)
    
    #wv_sendGPrim(<void*>wsi, context, buf, flag, callback, 
    #             <void *>f)
    


