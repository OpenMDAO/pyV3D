import os
import sys
import traceback

from numpy import array, float32, float64, int32, uint8

from tornado import websocket

from pyV3D._pyV3D import WV_Wrapper, WV_ON, WV_SHADING, WV_ORIENTATION

from pkg_resources import working_set

def ERROR(*args):
    for arg in args:
        sys.stderr.write(str(arg))
        sys.stderr.write(" ")
    sys.stderr.write('\n')
    sys.stderr.flush()

#def DEBUG(*args):
#    pass
DEBUG = ERROR

class WSHandler(websocket.WebSocketHandler):

    subhandlers = {}   # map of obj pathname or file pathname to subhandler instance
    protocols = {}   # map of protocols to lists of supporting subhandlers

    def initialize(self, view_dir):
        self.view_dir = os.path.expanduser(os.path.abspath(view_dir))
        self.subhandler = None

    def _handle_request_exception(self, exc):
        ERROR("Unhandled exception: %s" % str(exc))
        super(WSHandler, self)._handle_request_exception(exc)


    def _execute(self, transforms, *args, **kwargs):
        DEBUG("in _execute")
        self._args = [a for a in args if a.strip()]
        self._kwargs = kwargs.copy()
        args = args[1:]
        try:
            super(WSHandler, self)._execute(transforms, *args, **kwargs)
        except Exception as err:
            ERROR("%s" % str(err))

    def open(self):
        DEBUG("in open")

        try:
            args = self._args
            kwargs = self._kwargs

            # look for the sub handler to see if we've already created one with 
            # another protocol, e.g., pyv3d-bin-1.0 and pyv3d-txt-1.0
            self.subhandler = self.subhandlers.get(tuple(args))
            if self.subhandler is not None:
                DEBUG("subhandler already existed, adding protocol %s to it." % self._proto)

            if self.subhandler is None:
                DEBUG("creating a new subhandler for %s" % args)
                # try to create a subhandler matching the given protocol.  Take
                # the first one that succeeds
                DEBUG("matching klasses:", self.protocols.get(self._proto, []))
                for klass in self.protocols.get(self._proto, []):
                    DEBUG("trying to create a ",klass)
                    try:
                        self.subhandler = klass(self, *args, **kwargs)
                    except Exception as err:
                        DEBUG(err)
                        pass
                    else:
                        self.subhandlers[tuple(args)] = self.subhandler
                        break
                else:
                    ERROR("No viewhandlers found.")
                    return

            DEBUG("got a subhandler!")
            self.subhandler.open(self)
        except Exception as err:
            ERROR('Exception: %s' % traceback.format_exc())

    def on_message(self, message):
        if self.subhandler is None:
            self.send_error(404)
            return
        self.subhandler.on_message(message)

    def on_close(self):
        DEBUG("WebSocket closed (proto=%s" % self._proto)

    def select_subprotocol(self, subprotocols):
        DEBUG("in select_subprotocol")
        try:
            for p in subprotocols:
                if p in self.protocols:
                    self._proto = p
                    DEBUG("matched subproto %s" % p)
                    return p
            DEBUG("returning None for subproto choices: %s" % subprotocols)
        except Exception as err:
            ERROR("%s" % err)
        self._proto = None
        return None

    def find_file(self, fname):
        fpath = os.path.abspath(os.path.join(self.view_dir, fname))
        if not fpath.startswith(self.view_dir):
            return None  # don't allow access of files outside of view_dir
        if os.path.isfile(fpath):
            return fpath
        return None


class SubHandler(object):
    def __init__(self):
        self.handlers = {}  # need this to send the msgs

    def on_message(self, message):
        DEBUG("websocket got message: %s" % message)

    def on_close(self):
        DEBUG("WebSocket closed. addr=%s" % id(self))

    def open(self, handler):
        DEBUG("WebSocket opened. addr=%d" % id(self))
        if handler._proto in self.handlers:
            raise RuntimeError("this subhandler already has a handler for protocol %s" % handler._proto)
        self.handlers[handler._proto] = handler


class WV_ViewHandler(SubHandler):
    def __init__(self):
        super(WV_ViewHandler, self).__init__()

        self.wv = WV_Wrapper()
        self.buf = self.wv.get_bufflen()*'\0'

    @staticmethod
    def get_protocols():
        return ['pyv3d-bin-1.0', 'pyv3d-txt-1.0']

    def send_binary_data(self, wsi, buf, ibuf):
        try:
            handler = self.handlers['pyv3d-bin-1.0']
        except KeyError:
            raise RuntimeError("Can't send binary data. No registred binary protocol handler")
        try:
            handler.write_message(buf, binary=True)
        except Exception as err:
            ERROR("Exception in send_binary_data:", err)
            return -1
        return 0

    def send_geometry(self, first=False):
        self.wv.prepare_for_sends()

        if first:
            self.wv.send_GPrim(self, self.buf,  1, self.send_binary_data)  # send init packet
            self.wv.send_GPrim(self, self.buf, -1, self.send_binary_data)  # send initial suite of GPrims
        else:  #FIXME: add updating of GPRims here...
            pass

        self.wv.finish_sends()

    def open(self, handler):
        super(WV_ViewHandler, self).open(handler)
        try:
            if handler._proto == 'pyv3d-bin-1.0':
                self.create_geom()
                self.send_geometry(first=True)
        except Exception as err:
            ERROR('Exception: %s' % traceback.format_exc())


class CubeViewHandler(WV_ViewHandler):

    def __init__(self, handler, *args, **kwargs):
        super(CubeViewHandler, self).__init__()

        if args or kwargs:
            raise RuntimeError("CubViewHandler should have no args or kwargs. args=%s, kwargs=%s" % (args, kwargs))

    def create_geom(self):

        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)
        fov   = 30.0
        zNear = 1.0
        zFar  = 10.0

        bias = 0
        self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)
        self.wv.createBox("Box$1", WV_ON|WV_SHADING|WV_ORIENTATION, [0.,0.,0.])


def load_subhandlers():
    DEBUG("in load_subhandlers()")
    # find all of the installed pyv3d subhandlers
    for ep in working_set.iter_entry_points('pyv3d.subhandlers'):
        try:
            klass = ep.load()
        except Exception as err:
            ERROR("Entry point %s failed to load: %s" % (str(ep).split()[0], err))
        else:
            DEBUG('loaded entry point ',str(ep).split()[0])
            protos = klass.get_protocols()
            for proto in protos:
                WSHandler.protocols.setdefault(proto, []).append(klass)


