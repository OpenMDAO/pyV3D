
import os
import unittest
import tempfile

import numpy as np

from pyV3D import WV_Wrapper, ConnectivitiesError
from pyV3D.cube import CubeGeometry, CubeSender
from pyV3D.stl import STLSender
from pyV3D import get_bounding_box, get_focus, adjust_points


class WV_Test_Wrapper(WV_Wrapper):
    pass


class WV_test_Wrapper(WV_Wrapper):

    def __init__(self, fname):
        super(WV_test_Wrapper, self).__init__()
        self.binfile = open(fname, 'wb')

    def send(self, first=False):
        self.prepare_for_sends()

        if first:
            # send init packet
            self.send_GPrim(self, 1, self.send_binary_data)
            # send initial suite of GPrims
            self.send_GPrim(self, -1, self.send_binary_data)
        else:
            # send initial suite of GPrims
            self.send_GPrim(self, -1, self.send_binary_data)

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
            pass
            #shutil.rmtree(self.tdir)
        except:
            pass

    def _compare(self, s1, s2, name1, name2):
        if len(s1) != len(s2):
            self.fail("%s has different length than %s" % (name1, name2))

        for i in range(len(s1)):
            if s1[i] != s2[i]:
                self.fail(
                    "byte %d (at least) "
                    "differs between files %s and %s. "
                    "(%s != %s)" % (i, name1, name2, s1[i], s2[i]))

    def test_bounding_box(self):
        a = np.array([[-1, -1, -1], [1, 1, 1]], dtype=np.float32)
        b = np.array([[1, 1, 1], [2, 2, 2]], dtype=np.float32)

        bbox = get_bounding_box(a.flatten())
        self.assertTrue((a[::-1] == bbox).all())

        bbox = get_bounding_box(b.flatten())
        self.assertTrue((b[::-1] == bbox).all())

        bbox2 = get_bounding_box(bbox.flatten())
        self.assertTrue((bbox2 == bbox).all())

    def test_focus(self):
        #test for cube
        bounding_box = np.array([10, 10, 10, 0, 0, 0], dtype=np.float32)
        expected_focus = np.array([5, 5, 5, 5], dtype=np.float32)
        actual_focus = get_focus(bounding_box)

        self.assertEqual(expected_focus.all(), actual_focus.all())

        #test for box
        bounding_box = np.array(
            [1024, 512, 256, 0, 0, 0],
            dtype=np.float32)

        expected_focus = np.array([512, 256, 128, 512], dtype=np.float32)
        actual_focus = get_focus(bounding_box)

        self.assertEqual(expected_focus.all(), actual_focus.all())

        #Test for max coordinate being corrected
        #if coordinate values are shifted
        x_max_bounding_box = np.array(
            [512, 256, 128, 0, 0, 0],
            dtype=np.float32)

        y_max_bounding_box = np.array(
            [256, 512, 128, 0, 0, 0],
            dtype=np.float32)

        z_max_bounding_box = np.array(
            [256, 128, 512, 0, 0, 0],
            dtype=np.float32)

        x_max_expected_focus = np.array([256, 128, 64, 256], dtype=np.float32)
        y_max_expected_focus = np.array([128, 256, 64, 256], dtype=np.float32)
        z_max_expected_focus = np.array([128, 64, 256, 256], dtype=np.float32)

        x_max_actual_focus = get_focus(x_max_bounding_box)
        y_max_actual_focus = get_focus(y_max_bounding_box)
        z_max_actual_focus = get_focus(z_max_bounding_box)

        self.assertEqual(x_max_expected_focus.all(), x_max_actual_focus.all())
        self.assertEqual(y_max_expected_focus.all(), y_max_actual_focus.all())
        self.assertEqual(z_max_expected_focus.all(), z_max_actual_focus.all())

        #Test for not so clean bounding box
        bounding_box = np.array(
            [1024, 500, -340, -472, 1, -2000],
            dtype=np.float32)

        expected_focus = np.array(
            [788, 250.5, -1170, 1170],
            dtype=np.float32)

        actual_focus = get_focus(bounding_box)

        self.assertEqual(expected_focus.all(), actual_focus.all())

    def test_adjust_points(self):
        #Center should always be translated to the origin
        focus = np.array([10]*4, dtype=np.float32)
        center = np.array([10]*3, dtype=np.float32)

        origin = np.zeros((1, 3), dtype=np.float32)
        translated_center = adjust_points(focus, center)
        self.assertEqual(origin.all(), translated_center.all())

        #Bounding box coordinates should be translated
        #to be centerd about the origin
        pmax = np.array([100, 50, 25], dtype=np.float32)
        pmin = np.array([0, 0, 0], dtype=np.float32)

        new_pmin = np.array([-50, -25, -12.5], dtype=np.float32)
        new_pmax = np.array([50, 25, 12.5], dtype=np.float32)

        translated_pmin = adjust_points(focus, pmin)
        translated_pmax = adjust_points(focus, pmax)

        self.assertEqual(translated_pmin.all(), new_pmin.all())
        self.assertEqual(translated_pmax.all(), new_pmax.all())

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

    def test_ascii_stl(self):
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
        points = np.zeros((4, 3), dtype=np.float32).flatten()
        #Connectivities should be zero indexed

        good_triangles = np.array(
            [[0, 1, 2], [1, 2, 3]],
            dtype=int).flatten()

        #Connectivites should not refecerence points
        #outside of bounds [0,len(points)/3)
        bad_triangles = np.array(
            [[1, 2, 3], [2, 3, 4]],
            dtype=int).flatten()
        wrapper = WV_Test_Wrapper()
        CubeSender(wrapper)
        wrapper.set_face_data(points=points, tris=good_triangles, name="good")

        try:
            wrapper.set_face_data(points, bad_triangles, name="bad")
        except ConnectivitiesError:
            pass


if __name__ == "__main__":
    unittest.main()
