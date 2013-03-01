import os
import sys

from numpy import array, float32, float64, int32, uint8

from tornado import httpserver, web, escape, ioloop, websocket
from tornado.web import RequestHandler, StaticFileHandler

from argparse import ArgumentParser

from pygem_diamond import gem
from pygem_diamond.pygem import GEMParametricGeometry
from pyV3D.pyV3D import WV_Wrapper

#sample_file = os.path.join(os.path.dirname(__file__), "test", "sample.csm")
sample_file = os.path.join(os.path.dirname(__file__), "test", "box1.csm")

debug = True

if debug:
    def DEBUG(msg):
        print '<<<' + str(os.getpid()) + '>>> --', msg
else:
    def DEBUG(msg):
        pass

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_argument_parser():
    ''' create a parser for command line arguments
    '''
    parser = ArgumentParser(description='launch the test server')
    parser.add_argument('-p', '--port', type=int, dest='port', default=8000,
                        help='port to run server on')
    return parser

class BaseWSHandler(websocket.WebSocketHandler):
    def _handle_request_exception(self, exc):
        print "Unhandled exception:",str(exc)
        super(BaseWSHandler, self)._handle_request_exception(exc)

# Determining size of buf for websockets:
#    define MAX_MUX_RECURSION 2
#    define LWS_SEND_BUFFER_PRE_PADDING (4 + 10 + (2 * MAX_MUX_RECURSION))
#    define LWS_SEND_BUFFER_POST_PADDING 1
#     unsigned char buf[LWS_SEND_BUFFER_PRE_PADDING + 128 +
#                             LWS_SEND_BUFFER_POST_PADDING]
#
# so -> 4 + 10 + 2*2 + 128 + 1 = 147

class WSTextHandler(BaseWSHandler):
    def __init__(self, application, request, **kwargs):
        super(WSTextHandler, self).__init__(application, request, **kwargs)
    
    def open(self):
        print "text WebSocket opened"

    def on_message(self, message):
        print "text WS: got message: %s" % message
        #self.write_message(u"You said: " + message)

    def on_close(self):
        print "text WebSocket closed"

    # def select_subprotocol(self, subprotocols):
    #     print 'asked for subprotocols: %s' % subprotocols
    #     if "pyv3d-text/1.0" in subprotocols:
    #         return "pyv3d-text/1.0"
    #     return None


class WSBinaryHandler(BaseWSHandler):
    def __init__(self, application, request, **kwargs):
        self.idxs = []
        super(WSBinaryHandler, self).__init__(application, request, **kwargs)
    
    def open(self):
        print "binary WebSocket opened"
        try:
            self.create_geom()
        except Exception as err:
            print 'Exception:',str(err)

    def on_message(self, message):
        print "binary ws got message: %s" % message

    def on_close(self):
        print "binary WebSocket closed"

    # def select_subprotocol(self, subprotocols):
    #     print 'binary ws asked for subprotocols: %s' % subprotocols
    #     if "pyv3d-binary/1.0" in subprotocols:
    #         return "pyv3d-binary/1.0"
    #     return None

    def send_binary_data(self, wsi, buf, ibuf):
        try:
            print "In send_binary_data"
            print "length", len(buf)
            print "ibuf", ibuf
            print "buf type=", str(type(buf))
            self.write_message(buf, binary=True)

            for idx in self.idxs:
                print "removing GPrim %s" % idx
                self.myWV.remove_GPrim(idx)

            self.idxs = []
        except Exception as err:
            print "Exception:",str(err)
            return -1
        
        return 0

    def create_geom(self):

        self.my_param_geom = GEMParametricGeometry()
        self.my_param_geom.model_file = sample_file

        #self.myContext = gem.Context()
        #myModel = self.myContext.loadModel(sample_file)
        # server, filename, modeler, uptodate, myBReps, nparam, \
        #     nbranch, nattr = myModel.getInfo()

        # print 'len(myBReps) = ', len(myBReps)

        # myDRep = myModel.newDRep()

        self.myWV = myWV = WV_Wrapper()

        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)

        myWV.createContext(0, 30.0, 1.0, 10.0, eye, center, up)

        # for i,brep in enumerate(myBReps):
        #     # How many faces?
        #     box, typ, nnode, nedge, nloop, nface, nshell, nattr = brep.getInfo()
        #     print nface, "faces"

        #     name = "brep_%d" % (i+1)

        #     # Tesselate the brep
        #     # brep, maxang, maxlen, maxasg
        #     myDRep.tessellate(i+1, 0, 0, 0)

        #     self.idxs.extend(myWV.load_DRep(myDRep, i+1, nface, name=name))

        geom = self.my_param_geom.get_geometry()
        if geom is None:
            raise RuntimeError("can't get Geometry object")

        WV_ON = 1
        WV_SHADING = 4
        WV_ORIENTATION = 8
        myWV.createBox("Box$1", WV_ON|WV_SHADING|WV_ORIENTATION, [0.,0.,0.])
        #indices = myWV.load_geometry(geom)

        print 'prep for send'
        myWV.prepare_for_sends()

        buf = (3205696+19)*' '
        print 'sendGPrim'
        myWV.send_GPrim(self, buf, 1, self.send_binary_data)  # send init packet
        myWV.send_GPrim(self, buf, -1, self.send_binary_data)  # send initial suite of GPrims

        print 'finish sends'
        myWV.finish_sends()


def main():
    ''' Process command line arguments and run.
    '''
    parser = get_argument_parser()
    options, args = parser.parse_known_args()


    handlers = [
        web.url(r'/', WSTextHandler),
        web.url(r'/binary', WSBinaryHandler),
    ]

    app_settings = {
        'static_path':       APP_DIR,
        #'template_path':     os.path.join(APP_DIR, 'partials'),
        'debug':             True,
    }
   
    app = web.Application(handlers, **app_settings)

    http_server = httpserver.HTTPServer(app)
    http_server.listen(options.port)

    DEBUG('Serving on port %d' % options.port)
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        DEBUG('interrupt received, shutting down.')


if __name__ == '__main__':
    main()
