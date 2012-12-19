
# file: cwv.pxd

from numpy import ndarray

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
                    
    void wv_sendGPrim(void *wsi, wvContext *cntxt, unsigned char *buf, int flag, 
                      int (*wv_sendBinaryData)(void*, unsigned char*, int))