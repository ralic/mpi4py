# Very, very naive RE-based way for collecting declarations inside
# 'cdef extern from *' Cython blocks in in source files, and next
# generate compatibility headers for MPI-2 partially implemented or
# built, or MPI-1 implementations, perhaps providing a subset of MPI-2

from textwrap import dedent
import mpiregexes as Re

class Node(object):

    REGEX = None
    def match(self, line):
        m = self.REGEX.search(line)
        if m: return m.groups()
    match = classmethod(match)

    CONFIG = None
    HEADER = None

    HEADER_HEAD = """\
    #ifdef PyMPI_MISSING_%(name)s
    #if !defined(%(cname)s)
    """
    HEADER_TAIL = """
    #endif
    #endif

    """

    def init(self, name=None, **kargs):
        if name is not None:
            self.name = name.upper()
        self.__dict__.update(kargs)
    def config(self):
        return self.CONFIG % vars(self)
    def header(self):
        head = dedent(self.HEADER_HEAD)
        body = dedent(self.HEADER)
        tail = dedent(self.HEADER_TAIL)
        return (head+body+tail) % vars(self)

class NodeType(Node):
    CONFIG = '%(ctype)s v;'
    def __init__(self, ctype):
        self.init(name=ctype,
                  cname=ctype,
                  ctype=ctype,)

class NodeStruct(NodeType):
    REGEX  = Re.STRUCT_TYPE
    HEADER = """\
    typedef struct {
    %(cfields)s
    } %(ctype)s;"""

    def __init__(self, ctype, cfields):
        super(NodeStruct, self).__init__(ctype)
        self.cfields = '\n'.join(['  %s %s;' % field
                                  for field in cfields])

class NodeFuncType(NodeType):
    HEADER = 'typedef %(crett)s (%(cname)s)(%(cargs)s);'
    def __init__(self, crett, cname, cargs, calias=None):
        self.init(name=cname.upper(),
                  cname=cname,
                  ctype=cname+'*',)
        self.crett = crett
        self.cargs = cargs or 'void'
        if calias is not None:
            self.HEADER = '#define %(cname)s %(calias)s'
            self.calias = calias

class NodeValue(Node):
    CONFIG = '%(ctype)s v; v = %(cname)s;'
    HEADER = '#define %(cname)s (%(calias)s)'
    def __init__(self, ctype, cname, calias):
        self.init(name=cname,
                  cname=cname,
                  ctype=ctype,
                  calias=calias)

def ctypefix(ct):
    ct = ct.strip()
    ct = ct.replace('[][3]',' (*)[3]')
    ct = ct.replace('[]','*')
    return ct

class NodeFuncProto(Node):
    CONFIG = '%(crett)s v; v = %(cname)s(%(cargscall)s);'
    HEADER = ' '. join(['#define %(cname)s(%(cargsnamed)s)',
                        'PyMPI_UNAVAILABLE("%(name)s"%(comma)s%(cargsnamed)s)'])
    def __init__(self, crett, cname, cargs, calias=None):
        self.init(name=cname.upper(),
                  cname=cname)
        self.crett = crett
        if cargs == 'void': cargs = ''
        if cargs: cargs = cargs.split(',')
        else:     cargs = []
        self.cargstype = cargs
        nargs = len(cargs)
        if nargs: self.comma = ','
        else:     self.comma = ''
        cargscall = ['(%s)0' % ctypefix(a) for a  in cargs]
        self.cargscall = ','.join(cargscall)
        cargsnamed = ['a%d' % (a+1) for a in range(nargs)]
        self.cargsnamed = ','.join(cargsnamed)
        if calias is not None:
            self.HEADER = '#define %(cname)s %(calias)s'
            self.calias = calias

class IntegralType(NodeType):
    REGEX = Re.INTEGRAL_TYPE
    HEADER = dedent("""\
    typedef long PyMPI_%(ctype)s;
    #define %(ctype)s PyMPI_%(ctype)s""")

class OpaqueType(NodeType):
    REGEX = Re.OPAQUE_TYPE
    HEADER = 'typedef void *PyMPI_%(ctype)s;'
    HEADER = dedent("""\
    typedef void *PyMPI_%(ctype)s;
    #define %(ctype)s PyMPI_%(ctype)s""")

class StructType(NodeStruct):
    def __init__(self, ctype):
        cnames = ['MPI_SOURCE', 'MPI_TAG', 'MPI_ERROR']
        cfields = zip(['int']*3, cnames)
        super(StructType, self).__init__(ctype, cfields)

class FunctionType(NodeFuncType):
    REGEX = Re.FUNCTION_TYPE

class EnumValue(NodeValue):
    REGEX = Re.ENUM_VALUE
    def __init__(self, cname, calias):
        self.init(name=cname,
                  cname=cname,
                  ctype='int',
                  calias=calias)


class HandleValue(NodeValue):
    REGEX = Re.HANDLE_VALUE
    HEADER = '#define %(cname)s ((%(ctype)s)%(calias)s)'

class BasicValuePtr(NodeValue):
    REGEX = Re.BASICP_VALUE

class StructValuePtr(NodeValue):
    REGEX = Re.STRUCTP_VALUE

class FunctionValuePtr(NodeValue):
    REGEX = Re.FUNCTP_VALUE

class FunctionProto(NodeFuncProto):
    REGEX = Re.FUNCTION_PROTO



class Scanner(object):

    NODE_TYPES = [
        IntegralType, StructType, OpaqueType,
        HandleValue, EnumValue,
        BasicValuePtr, StructValuePtr,
        FunctionType, FunctionValuePtr,
        FunctionProto,
        ]
    def __init__(self):
        self.nodes = []
        self.nodemap = {}

    def parse_file(self, filename):
        fileobj = open(filename)
        try: self.parse_lines(fileobj)
        finally: fileobj.close()

    def parse_lines(self, lines):
        for line in lines:
            self.parse_line(line)

    def parse_line(self, line):
        nodemap  = self.nodemap
        nodelist = self.nodes
        for nodetype in self.NODE_TYPES:
            args = nodetype.match(line)
            if args:
                node = nodetype(*args)
                assert node.name not in nodemap
                nodemap[node.name] = len(nodelist)
                nodelist.append(node)
                break

    def __iter__(self):
        return iter(self.nodes)

    def itertests(self):
        for node in self:
            yield (node.name, node.config())


    CONFIG_HEAD = """\
    #ifndef PyMPI_CONFIG_H
    #define PyMPI_CONFIG_H

    """
    CONFIG_MACRO = '#define PyMPI_MISSING_%s 1\n'
    CONFIG_TAIL = """\

    #endif /* !PyMPI_CONFIG_H */
    """
    def dump_config_h(self, fileobj, suite):
        if isinstance(fileobj, str):
            fileobj = open(fileobj, 'w')
            try: self.dump_config_h(fileobj, suite)
            finally: fileobj.close()
            return
        head  = dedent(self.CONFIG_HEAD)
        macro = dedent(self.CONFIG_MACRO)
        tail  = dedent(self.CONFIG_TAIL)
        fileobj.write(head)
        if suite is None:
            for node in self:
                fileobj.write(macro % node.name)
        else:
            for name, result in suite:
                assert name in self.nodemap
                if not result:
                    fileobj.write(macro % name)
        fileobj.write(tail)

    MISSING_HEAD = """\
    #ifndef PyMPI_MISSING_H
    #define PyMPI_MISSING_H

    #ifndef PyMPI_UNUSED
    # if defined(__GNUC__)
    #   if !defined(__cplusplus) || (__GNUC__ > 3 || (__GNUC__ == 3 && __GNUC_MINOR__ >= 4))
    #     define PyMPI_UNUSED __attribute__ ((__unused__))
    #   else
    #     define PyMPI_UNUSED
    #   endif
    # elif defined(__INTEL_COMPILER) || defined(__ICC)
    #   define PyMPI_UNUSED __attribute__ ((__unused__))
    # else
    #   define PyMPI_UNUSED
    # endif
    #endif

    static PyMPI_UNUSED int PyMPI_UNAVAILABLE(const char *name,...)
    {
      /* XXX do someting with name */
      return -1;
    }

    """
    MISSING_TAIL = """\
    #endif /* !PyMPI_MISSING_H */
    """
    def dump_missing_h(self, fileobj, suite):
        if isinstance(fileobj, str):
            fileobj = open(fileobj, 'w')
            try: self.dump_missing_h(fileobj, suite)
            finally: fileobj.close()
            return
        head = dedent(self.MISSING_HEAD)
        tail = dedent(self.MISSING_TAIL)
        #
        fileobj.write(head)
        if suite is None:
            for node in self:
                fileobj.write(node.header())
        else:
            nodelist = self.nodes
            nodemap = self.nodemap
            for name, result in suite:
                assert name in nodemap
                if not result:
                    node = nodelist[nodemap[name]]
                    fileobj.write(node.header())
        fileobj.write(tail)


# -----------------------------------------


if __name__ == '__main__':
    sources = ['mpi.pxi']
    import sys, os
    log = lambda msg: sys.stderr.write(msg + '\n')
    scanner = Scanner()
    for filename in sources:
        filename = os.path.join('src', 'mpi4py', filename)
        log('parsing file %s' % filename)
        scanner.parse_file(filename)
    log('processed %d definitions' % len(scanner.nodes))
    config_h  = os.path.join('src', 'config.h')
    missing_h = os.path.join('src', 'missing.h')
    log('writing file %s' % config_h)
    scanner.dump_config_h(config_h, None)
    log('writing file %s' % missing_h)
    scanner.dump_missing_h(missing_h, None)

# -----------------------------------------