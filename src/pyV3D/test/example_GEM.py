
import os 

from numpy import array, float32, int32, uint8

from pygem_diamond import gem
from pygem_diamond.pygem import GEMParametricGeometry
from pyV3D.pyV3D import WV_Wrapper

sample_file = os.path.join(os.path.dirname(__file__), "sample.csm")

def send_binary_data(wsi, buf, ibuf):
    print "In send_binary_data"
    print "length", len(buf)
    print "buffer", [buf[i] for i in range(0, ibuf)]
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
            
            
myContext = gem.Context()
myModel = myContext.loadModel(sample_file)
server, filename, modeler, uptodate, myBReps, nparam, \
    nbranch, nattr = myModel.getInfo()

iBRep = 0;

# How many faces?
box, typ, nnode, nedge, nloop, nface, nshell, nattr = myBReps[iBRep].getInfo()
print nface, "faces"

myDRep = myModel.newDRep()

# Tesselate our brep
# brep, maxang, maxlen, maxasg
myDRep.tesselate(iBRep, 0, 0, 0)

#triArray, xyzArray = myDRep.getTessel(1, 1)

myWV = WV_Wrapper()

eye    = array([1.0, 0.0, 7.0], dtype=float32)
center = array([0.0, 0.0, 0.0], dtype=float32)
up     = array([0.0, 1.0, 0.0], dtype=float32)

myWV.createContext(0, 30.0, 1.0, 10.0, eye, center, up)

myWV.load_DRep(myDRep, iBRep+1, nface, name="MyBox")

buf = 146*' '
wsi = wsi_server()
myWV.prepare_for_sends()
#myWV.send_GPrim(wsi, buf, 1, send_binary_data)
#myWV.send_GPrim(wsi, buf, 0, send_binary_data)
myWV.send_GPrim(wsi, buf, -1, send_binary_data)
myWV.finish_sends()

myWV.remove_GPrim(0)