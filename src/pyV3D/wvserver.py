import os
import sys
import traceback

from numpy import array, float32, float64, int32, uint8

from tornado import httpserver, web, escape, ioloop, websocket
from tornado.web import RequestHandler, StaticFileHandler

from argparse import ArgumentParser

from pyV3D.pyV3D import WV_Wrapper

#sample_file = os.path.join(os.path.dirname(__file__), "test", "sample.csm")
#sample_file = os.path.join(os.path.dirname(__file__), "test", "box1.csm")

options = None

def ERROR(*args):
    for arg in args:
        sys.stderr.write(str(arg))
        sys.stderr.write(" ")
    sys.stderr.write('\n')

def DEBUG(*args):
    pass

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_argument_parser():
    ''' create a parser for command line arguments
    '''
    parser = ArgumentParser(description='launch the test server')
    parser.add_argument('-p', '--port', type=int, dest='port', default=8000,
                        help='port to run server on')
    parser.add_argument("-d","--debug", action="store_true", dest='debug',
                        help="turn on debug mode")
    parser.add_argument('geometry_file', nargs='?',
                        help='pathname of geometry file to view')
    return parser

class BaseWSHandler(websocket.WebSocketHandler):
    def _handle_request_exception(self, exc):
        ERROR("Unhandled exception: %s" % str(exc))
        super(BaseWSHandler, self)._handle_request_exception(exc)

class WSTextHandler(BaseWSHandler):
    def open(self):
        DEBUG("text WebSocket opened")

    def on_message(self, message):
        DEBUG("text WS: got message: %s" % message)
        #self.write_message(u"You said: " + message)

    def on_close(self):
        DEBUG("text WebSocket closed")

    # def select_subprotocol(self, subprotocols):
    #     print 'asked for subprotocols: %s' % subprotocols
    #     if "pyv3d-text/1.0" in subprotocols:
    #         return "pyv3d-text/1.0"
    #     return None


class WSBinaryHandler(BaseWSHandler):
    def open(self):
        DEBUG("binary WebSocket opened")
        try:
            self.create_geom()
        except Exception as err:
            ERROR('Exception: %s' % traceback.format_exc())

    def on_message(self, message):
        DEBUG("binary ws got message: %s" % message)

    def on_close(self):
        DEBUG("binary WebSocket closed")

    # def select_subprotocol(self, subprotocols):
    #     print 'binary ws asked for subprotocols: %s' % subprotocols
    #     if "pyv3d-binary/1.0" in subprotocols:
    #         return "pyv3d-binary/1.0"
    #     return None

    def send_binary_data(self, wsi, buf, ibuf):
        try:
            self.write_message(buf, binary=True)
        except Exception as err:
            ERROR("Exception in send_binary_data:", err)
            return -1
        
        return 0

    def create_geom(self):

        myWV = WV_Wrapper()
        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)
        fov   = 30.0
        zNear = 1.0
        zFar  = 10.0

        if options.geometry_file:

            if options.geometry_file.endswith('.csm'):
                try:
                    from pygem_diamond import gem
                    from pygem_diamond.pygem import GEMParametricGeometry
                except ImportError:
                    sys.stderr.write("\nviewing opencsm files requires the pygem_diamond package\n")
                    sys.exit(-1)

                bias  = 1
                myWV.createContext(bias, fov, zNear, zFar, eye, center, up)

                self.my_param_geom = GEMParametricGeometry()
                self.my_param_geom.model_file = os.path.expanduser(os.path.abspath(options.geometry_file))
                geom = self.my_param_geom.get_geometry()
                if geom is None:
                    raise RuntimeError("can't get Geometry object")
                myWV.load_geometry(geom, angle=15., relSide=.02, relSag=.001)
            else:
                sys.stderr.write("\nunrecognized geometry file extension\n")
                sys.exit(-1)
        else:
            bias = 0
            myWV.createContext(bias, fov, zNear, zFar, eye, center, up)
            WV_ON = 1
            WV_SHADING = 4
            WV_ORIENTATION = 8
            myWV.createBox("Box$1", WV_ON|WV_SHADING|WV_ORIENTATION, [0.,0.,0.])

        DEBUG('prep for send')
        myWV.prepare_for_sends()

        buf = myWV.get_bufflen()*'\0'
        DEBUG('buff len = %d' % len(buf))
        DEBUG('sendGPrim')
        myWV.send_GPrim(self, buf, 1, self.send_binary_data)  # send init packet
        DEBUG('init packet done')
        myWV.send_GPrim(self, buf, -1, self.send_binary_data)  # send initial suite of GPrims

        DEBUG('finish sends')
        myWV.finish_sends()


def main():
    ''' Process command line arguments and run.
    '''
    global DEBUG
    global options

    parser = get_argument_parser()
    options, args = parser.parse_known_args()

    if options.debug:
        DEBUG = ERROR

    handlers = [
        web.url(r'/', WSTextHandler),
        web.url(r'/binary', WSBinaryHandler),
    ]

    app_settings = {
        'static_path':       APP_DIR,
        'debug':             True,
    }
   
    app = web.Application(handlers, **app_settings)

    http_server = httpserver.HTTPServer(app)
    http_server.listen(options.port)

    print 'Serving on port %d' % options.port
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        DEBUG('interrupt received, shutting down.')


if __name__ == '__main__':
    main()
