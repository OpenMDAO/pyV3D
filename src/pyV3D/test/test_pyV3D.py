
import os
import unittest
import tempfile
import shutil

import numpy as np

from pyV3D import WV_Wrapper, ConnectivitiesError
from pyV3D.cube import CubeGeometry, CubeSender
from pyV3D.stl import STLSender

class WV_Test_Wrapper(WV_Wrapper):
    pass

class WV_test_Wrapper(WV_Wrapper):

    def __init__(self, fname):
        super(WV_test_Wrapper, self).__init__()
        self.binfile = open(fname, 'wb')

    def send(self, first=False):
        self.prepare_for_sends()

        if first:
            self.send_GPrim(self, 1, self.send_binary_data)  # send init packet
            self.send_GPrim(self, -1, self.send_binary_data)  # send initial suite of GPrims
        else:  
            self.send_GPrim(self, -1, self.send_binary_data)  # send initial suite of GPrims

        self.finish_sends()
        
    def send_binary_data(self, wsi, buf, ibuf):
        """This is called multiple times during the sending of a 
        set of graphics primitives.
        """
        self.binfile.write(buf)
        return 0


class PyV3DTestCase(unittest.TestCase):

    def setUp(self):
        self.tdir = tempfile.mkdtemp()
        self.path = os.path.dirname(os.path.abspath(__file__))
        
    def tearDown(self):
        try:
            shutil.rmtree(self.tdir)
        except:
            pass

    def _compare(self, s1, s2, name1, name2):
        if len(s1) != len(s2):
            self.fail("%s has different length than %s" % (name1, name2))
        
        for i in range(len(s1)):
            if s1[i] != s2[i]:
                self.fail("byte %d (at least) differs between files %s and %s. (%s != %s)" % 
                              (i, name1, name2, s1[i], s2[i]))

    def test_cube(self):
        cname = os.path.join(self.path, 'cube.bin')
        newname = os.path.join(self.tdir, 'cube.bin')

        sender = CubeSender(WV_test_Wrapper(newname))
        sender.send(CubeGeometry(), first=True)
        sender.wv.binfile.close()

        with open(cname) as f:
            content = f.read()
        with open(newname) as f:
            newcontent = f.read()
        self._compare(content, newcontent, cname, newname)
        
    def test_stl(self):
        cname = os.path.join(self.path, 'star.bin')
        newname = os.path.join(self.tdir, 'star.bin')

        sender = STLSender(WV_test_Wrapper(newname))
        sender.send(os.path.join(self.path, 'star.stl'), first=True)
        sender.wv.binfile.close()

        with open(cname) as f:
            content = f.read()
        with open(newname) as f:
            newcontent = f.read()
        self._compare(content, newcontent, cname, newname)
    
    def test_binary_stl(self):
        cname = os.path.join(self.path, 'knot.bin')
        newname = os.path.join(self.tdir, 'knot.bin')

        sender = STLSender(WV_test_Wrapper(newname))

        import pdb
        pdb.set_trace()
        sender.send(os.path.join(self.path, 'knot.stl'), first=True)
        sender.wv.binfile.close()

        with open(cname) as f:
            content = f.read()
        with open(newname) as f:
            newcontent = f.read()
        self._compare(content, newcontent, cname, newname)

    def test_checkConnectivities(self):
        '''
        Test for geometry with a single face with 4 points and two triangles
         p0 *--* p3
            | /|   
            |/ |
         p1 *--* p2
        '''

        #Points are zero indexed
        points = np.zeros((4,3),dtype=np.float32).flatten()
       
        #Connectivities should be zero indexed
        good_triangles = np.array([[0,1,2],[1,2,3]], dtype=int).flatten()

        #Connectivites should not refecerence points outside of bounds [0,len(points)/3)
        bad_triangles = np.array([[1,2,3],[2,3,4]], dtype=int).flatten()
        wrapper = WV_Test_Wrapper()
        sender = CubeSender(wrapper) 
        wrapper.set_face_data(points=points, tris=good_triangles, name="good")

        try:
            wrapper.set_face_data(points, bad_triangles, name="bad")
        except ConnectivitiesError:
            pass
            
if __name__ == "__main__":
    unittest.main()
