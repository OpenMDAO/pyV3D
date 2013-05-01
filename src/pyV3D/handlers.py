import os
import sys
import traceback
from threading import Lock

from numpy import array, float32

from tornado import websocket

from pyV3D._pyV3D import WV_Wrapper, WV_ON, WV_SHADING, WV_ORIENTATION

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
    protocols   = {}   # map of protocols to lists of supporting subhandlers
    _lock = Lock()

    def initialize(self, view_dir):
        DEBUG("view dir = %s" % view_dir)
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
            ERROR("%s" % err)
        self._protocol = None
        return None

    def open(self):
        try:
            args = self._args
            kwargs = self._kwargs

            with self._lock:
            # look for the subhandler to see if we've already created one with 
            # another protocol, e.g., pyv3d-bin-1.0 and pyv3d-txt-1.0
                self.subhandler = self.subhandlers.get(tuple(args))
                if self.subhandler is not None:
                    DEBUG("subhandler already existed, adding protocol %s to it." % self._protocol)

                if self.subhandler is None:
                    DEBUG("creating a new subhandler for %s" % args)
                    # try to create a subhandler matching the given protocol.  Take
                    # the first one that succeeds.  This means that subhandlers MUST
                    # raise an exception if they are not able to successfully construct themselves.
                    for klass in self.protocols.get(self._protocol, []):
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
            ERROR("no subhandler to handle message")
            return
        self.subhandler.on_message(self, message)

    def on_close(self):
        try:
            if self.subhandler:
                self.subhandler.on_close(self)
        finally:
            with self._lock:
                for key,val in self.subhandlers.items():
                    if val is self.subhandler:
                        del self.subhandlers[key]
                        break

        DEBUG("WebSocket closed (proto=%s)" % self._protocol)

    def select_subprotocol(self, subprotocols):
        DEBUG("in select_subprotocol")
        try:
            for p in subprotocols:
                if p in self.protocols:
                    self._protocol = p
                    DEBUG("matched subproto %s" % p)
                    return p
            DEBUG("returning None for subproto choices: %s" % subprotocols)
        except Exception as err:
            ERROR("%s" % err)
        self._protocol = None
        return None

    def find_file(self, fname):
        fpath = os.path.abspath(os.path.join(self.view_dir, fname))
        if not fpath.startswith(self.view_dir):
            return None  # don't allow access of files outside of view_dir
        if os.path.isfile(fpath):
            return fpath
        return None


class SubHandler(object):
    """This class exists so that we can have the same handler for multiple websocket
    subprotocols.  This makes it easier to write pyV3D viewers because pyV3D requires
    a text protocol and a binary protocol.  Each subprotocol is handled by a separate
    websocket handler in tornado.  Instances that inherit from this class will receive
    callbacks from both websocket handlers.
    """
    def __init__(self):
        self.handlers = {}  # need real websocket handler(s) to send msgs

    def on_message(self, handler, message):
        DEBUG("websocket subhandler got message for protocol (%s): %s" % (handler._protocol, message))

    def on_close(self, handler):
        DEBUG("WebSocket subhandler closed for protocol %s" % handler._protocol)

    def open(self, handler):
        DEBUG("WebSocket subhandler opened for protocol %s" % handler._protocol)
        if handler._protocol in self.handlers:
            raise RuntimeError("this subhandler already has a handler for protocol %s" % handler._protocol)
        self.handlers[handler._protocol] = handler



class WV_ViewHandler(SubHandler):
    def __init__(self, wv):
        super(WV_ViewHandler, self).__init__()
        self.wv = wv

    @staticmethod
    def get_protocols():
        """Returns a list of supported protocols."""
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
            if handler._protocol == 'pyv3d-bin-1.0':
                self.create_geom()
                self.send_geometry(first=True)
        except Exception:
            ERROR('Exception: %s' % traceback.format_exc())


class WS_WV_Wrapper(WV_Wrapper):
    """A wrapper for the wv library that sends updates out over
    a WebSocket.
    """
    
    def __init__(self):
        super(WS_WV_Wrapper, self).__init__()
       
        # TODO: make this buffer internal to WV_Wrapper
        self.buf = self.get_bufflen()*b'\0'

    def send(self, first=False):
        self.prepare_for_sends()

        if first:
            self.send_GPrim(self, self.buf,  1, self.send_binary_data)  # send init packet
            self.send_GPrim(self, self.buf, -1, self.send_binary_data)  # send initial suite of GPrims
        else:  
            self.send_GPrim(self, self.buf, -1, self.send_binary_data)  # send initial suite of GPrims

        self.finish_sends()
        
    def send_binary_data(self, wsi, buf, ibuf):
        """This is called multiple times during the sending of a 
        set of graphics primitives.
        """
        logger.error("send_binary_data: , objname='%s', ibuf=%d" % (self.objname, ibuf))
        try:
            publish(self.objname, buf, binary=True)
        except Exception:
            logger.error(traceback.format_exc())
            return -1
        return 0

class Sender(object):
    def send(self, first=False):
        raise NotImplementedError('send')


class WV_Sender(Sender):
    def __init__(self, wv, **kwargs):
        self.wv = wv
        self.initialize(**kwargs)

    def initialize(self, **kwargs):
        pass

    def send(self, obj, first=False):
        if not first:
            self.wv.clear()  # clear out old GPrim data

        if isinstance(obj, basestring): # assume it's a filename
            self.geom_from_file(obj)
        else:
            self.geom_from_obj(obj)
        self.wv.send(first)

    def geom_from_file(self, fname):
        raise NotImplementedError("geom_from_file")
    
    def geom_from_obj(self, obj):
        raise NotImplementedError("geom_from_obj")


class CubeSender(WV_Sender):
    """This is just here for demo purposes so that something can be viewed even
    if no real binpub plugins have been installed.
    """

    def initialize(self, **kwargs):
        eye    = array([0.0, 0.0, 7.0], dtype=float32)
        center = array([0.0, 0.0, 0.0], dtype=float32)
        up     = array([0.0, 1.0, 0.0], dtype=float32)
        fov   = 30.0
        zNear = 1.0
        zFar  = 10.0

        bias = 0
        self.wv.createContext(bias, fov, zNear, zFar, eye, center, up)

    @staticmethod
    def supports(obj):
        return obj is None

    def geom_from_obj(self, obj):
        self.wv.createBox("Box$1", WV_ON|WV_SHADING|WV_ORIENTATION, [0.,0.,0.])



