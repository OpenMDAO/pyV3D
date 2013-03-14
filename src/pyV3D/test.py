
from pyV3D.pyV3D import WV_Wrapper
from numpy import array, float64, float32, int32, uint8


myWV = WV_Wrapper()

eye    = array([1.0, 0.0, 7.0], dtype=float32)
center = array([0.0, 0.0, 0.0], dtype=float32)
up     = array([0.0, 1.0, 0.0], dtype=float32)

myWV.createContext(0, 30.0, 1.0, 10.0, eye, center, up)

# box
# v6----- v5
# /| /|
# v1------v0|
# | | | |
# | |v7---|-|v4
# |/ |/
# v2------v3
#
# vertex coords array
vertices = [
    1, 1, 1, -1, 1, 1, -1,-1, 1, 1,-1, 1, # v0-v1-v2-v3 front
    1, 1, 1, 1,-1, 1, 1,-1,-1, 1, 1,-1, # v0-v3-v4-v5 right
    1, 1, 1, 1, 1,-1, -1, 1,-1, -1, 1, 1, # v0-v5-v6-v1 top
   -1, 1, 1, -1, 1,-1, -1,-1,-1, -1,-1, 1, # v1-v6-v7-v2 left
   -1,-1,-1, 1,-1,-1, 1,-1, 1, -1,-1, 1, # v7-v4-v3-v2 bottom
    1,-1,-1, -1,-1,-1, -1, 1,-1, 1, 1,-1 ] # v4-v7-v6-v5 back

# normal array
normals = [
    0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, # v0-v1-v2-v3 front
    1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, # v0-v3-v4-v5 right
    0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, # v0-v5-v6-v1 top
   -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, # v1-v6-v7-v2 left
    0,-1, 0, 0,-1, 0, 0,-1, 0, 0,-1, 0, # v7-v4-v3-v2 bottom
    0, 0,-1, 0, 0,-1, 0, 0,-1, 0, 0,-1 ] # v4-v7-v6-v5 back

# color array
colors = [
    0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0, 255, # v0-v1-v2-v3
    255, 0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0, # v0-v3-v4-v5
    0, 255, 0, 0, 255, 0, 0, 255, 0, 0, 255, 0, # v0-v5-v6-v1
    255, 255, 0, 255, 255, 0, 255, 255, 0, 255, 255, 0, # v1-v6-v7-v2
    255, 0, 255, 255, 0, 255, 255, 0, 255, 255, 0, 255, # v7-v4-v3-v2
    0, 255, 255, 0, 255, 255, 0, 255, 255, 0, 255, 255] # v4-v7-v6-v5

# index array
indices = [
    0, 1, 2, 0, 2, 3, # front
    4, 5, 6, 4, 6, 7, # right
    8, 9,10, 8,10,11, # top
   12,13,14, 12,14,15, # left
   16,17,18, 16,18,19, # bottom
   20,21,22, 20,22,23 ] # back


vertices = array(vertices, dtype=float32)
indices = array(indices, dtype=int32)
colors = array(colors, dtype=uint8)
normals = array(normals, dtype=float32)

myWV.add_GPrim_solid("MyBox", vertices, indices, colors, normals,
                     shading=True, orientation=True)
#myWV.add_GPrim_solid("MyBox", vertices, indices,
#                     shading=True, orientation=True)

# Determining size of buf for websockets:
#    define MAX_MUX_RECURSION 2
#    define LWS_SEND_BUFFER_PRE_PADDING (4 + 10 + (2 * MAX_MUX_RECURSION))
#    define LWS_SEND_BUFFER_POST_PADDING 1
#     unsigned char buf[LWS_SEND_BUFFER_PRE_PADDING + 320569 +
#                             LWS_SEND_BUFFER_POST_PADDING]
#
# so -> 4 + 10 + 2*2 + 3205696 + 1 = 3205715

def send_binary_data(wsi, buf, ibuf):
    print "In send_binary_data"
    print "length", len(buf)
    print "buffer", [buf[i] for i in range(0, ibuf)]
    print ibuf
    wsi.check()
    
    return 0

class wsi_server(object):
    
    def check(self):
        print "Hello from the Server"
        
    def write_to_file(self, name, buf):
        ''' Writes the binary data to a file
        '''
        
        with open(name, 'wb') as out:
            out.write(buf)

buf = 3205696*' '
wsi = wsi_server()
myWV.prepare_for_sends()
#myWV.send_GPrim(wsi, buf, 1, send_binary_data)
#myWV.send_GPrim(wsi, buf, 0, send_binary_data)
myWV.send_GPrim(wsi, buf, -1, send_binary_data)
myWV.finish_sends()
myWV.remove_GPrim(0)
