
cdef extern from "wsss.h":

  struct wvContext:
    int     gtype
    int     updateFlg


# /*@null@*/ wvContext *
cdef wv_createContext(int bias, float fov, float zNear, float zFar, float *eye,
                      float *center, float *up)

  wvContext *context;

  context = (wvContext *) wv_alloc(sizeof(wvContext));
  if (context == NULL) return NULL;

  context.ioAccess   = 0;
  context.dataAccess = 0;
  context.bias       = bias;
  context.fov        = fov;
  context.zNear      = zNear;
  context.zFar       = zFar;
  context.eye[0]     = eye[0];
  context.eye[1]     = eye[1];
  context.eye[2]     = eye[2];
  context.center[0]  = center[0];
  context.center[1]  = center[1];
  context.center[2]  = center[2];
  context.up[0]      = up[0];
  context.up[1]      = up[1];
  context.up[2]      = up[2];
  context.cleanAll   = 0;
  context.nGPrim     = 0;
  context.mGPrim     = 0;
  context.gPrims     = NULL;

  return context;
