from pyV3D.pyV3D import WV_Wrapper, STLGeometryObject

from numpy import array, float32

def send_binary_data(wsi, buf, ibuf):
    print "In send_binary_data"
    print "length", len(buf)
    #print "buffer", [buf[i] for i in range(0, ibuf)]
    print ibuf
    wsi.check()
    wsi.write_to_file('cube.bin', buf)
    
    return 0

class wsi_server(object):
    
    def check(self):
        print "Hello from the Server"
        
    def write_to_file(self, name, buf):
        ''' Writes the binary data to a file
        '''
        
        with open(name, 'wb') as out:
            out.write(buf)
            
myWV = WV_Wrapper()

eye    = array([1.0, 0.0, 7.0], dtype=float32)
center = array([0.0, 0.0, 0.0], dtype=float32)
up     = array([0.0, 1.0, 0.0], dtype=float32)

myWV.createContext(0, 30.0, 1.0, 10.0, eye, center, up)

#myGeometry = STLGeometryObject("sr22.stl") 
myGeometry = STLGeometryObject("porsche.stl") 
myGeometry.get_visualization_data(myWV)

wsi = wsi_server()
myWV.prepare_for_sends()
myWV.send_GPrim(wsi, 1, send_binary_data)
myWV.send_GPrim(wsi, -1, send_binary_data)
myWV.finish_sends()

myWV.remove_GPrim(0)
