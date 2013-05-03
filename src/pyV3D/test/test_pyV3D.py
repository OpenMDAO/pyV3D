
import os
import unittest
import tempfile
import shutil

from pyV3D import WV_Wrapper
from pyV3D.cube import CubeSender


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
            
    def test_PyV3D(self):
        sender = CubeSender(WV_test_Wrapper)
        
        
if __name__ == "__main__":
    unittest.main()
