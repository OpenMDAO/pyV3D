
from pyV3D import WV_Wrapper
from array import array


myWV = WV_Wrapper()

eye    = array('d', [1.0, 0.0, 7.0])
center = array('d', [0.0, 0.0, 0.0])
up     = array('d', [0.0, 1.0, 0.0])

myWV.wv_createContext(0, 30.0, 1.0, 10.0, eye, center, up)