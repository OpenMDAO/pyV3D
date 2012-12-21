#
#   Cython wrapper for the cheesefinder API
#

cdef extern from "cheesefinder.h":
    ctypedef int (*cheesefunc)(char *name, void *user_data)
    void find_cheeses(cheesefunc user_func, void *user_data)

def find(f):
    find_cheeses(callback, <void*>f)
    
cdef int callback(char *name, void *f):
    z = (<object>f)(name)
    print "This is", z, type(z)
    return z
