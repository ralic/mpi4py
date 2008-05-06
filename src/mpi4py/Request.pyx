cdef class Request:

    """
    Request
    """

    def __cinit__(self):
        self.ob_mpi = MPI_REQUEST_NULL

    def __dealloc__(self):
        cdef int ierr = 0
        ierr = _del_Request(&self.ob_mpi); CHKERR(ierr)

    def __richcmp__(Request self, Request other, int op):
        if op == 2:
            return (self.ob_mpi == other.ob_mpi)
        elif op == 3:
            return (self.ob_mpi != other.ob_mpi)
        else:
            raise TypeError("only '==' and '!='")

    def __nonzero__(self):
        return self.ob_mpi != MPI_REQUEST_NULL

    def __bool__(self):
        return self.ob_mpi != MPI_REQUEST_NULL

    # Completion Operations
    # ---------------------

    def Wait(self, status=None):
        """
        Wait for an MPI send or receive to complete.
        """
        cdef MPI_Status *statusp = _arg_Status(status)
        CHKERR( MPI_Wait(&self.ob_mpi, statusp) )

    def Test(self, status=None):
        """
        Test for the completion of a send or receive.
        """
        cdef bint flag = 0
        cdef MPI_Status *statusp = _arg_Status(status)
        CHKERR( MPI_Test(&self.ob_mpi, &flag, statusp) )
        return flag

    def Free(self):
        """
        Free a communication request
        """
        CHKERR( MPI_Request_free(&self.ob_mpi) )

    def Get_status(self, status=None):
        """
        Non-destructive test for the
        completion of a request
        """
        cdef bint flag = 0
        cdef MPI_Status *statusp = _arg_Status(status)
        CHKERR( MPI_Request_get_status(self.ob_mpi, &flag, statusp) )
        return flag

    # Multiple Completions
    # --------------------

    ## @classmethod
    def Waitany(cls, requests, status=None):
        """
        Wait for any previously initiated request to complete
        """
        cdef int count = len(requests)
        cdef MPI_Request *irequests = NULL
        cdef tmp1 = asarray_Request(requests, &irequests, count)
        cdef MPI_Status *statusp = _arg_Status(status)
        cdef int index = MPI_UNDEFINED
        # do not use CHKERR() directly !!
        cdef int ierr = MPI_Waitany(count, irequests, &index, statusp)
        tmp1 = restore_Request(requests, &irequests, count);
        CHKERR(ierr) # do error checking here
        #
        return index

    Waitany = classmethod(Waitany)

    ## @classmethod
    def Testany(cls, requests, status=None):
        """
        Test for completion of any previously initiated request
        """
        cdef int count = len(requests)
        cdef MPI_Request *irequests = NULL
        cdef tmp1 = asarray_Request(requests, &irequests, count)
        cdef int index = MPI_UNDEFINED
        cdef bint flag = 0
        cdef MPI_Status *statusp = _arg_Status(status)
        # do not use CHKERR() directly !!
        cdef int ierr = MPI_Testany(count, irequests,
                                    &index, &flag, statusp)
        tmp1 = restore_Request(requests, &irequests, count)
        CHKERR(ierr) # do error checking here
        #
        return (index, flag)

    Testany = classmethod(Testany)

    ## @classmethod
    def Waitall(cls, requests, statuses=None):
        """
        Wait for all previously initiated requests to complete
        """
        cdef int count = len(requests)
        cdef MPI_Request *irequests = NULL
        cdef tmp1 = asarray_Request(requests, &irequests, count)
        cdef MPI_Status *istatuses = MPI_STATUSES_IGNORE
        cdef tmp2 = asarray_Status(statuses, &istatuses, count)
        # do not use CHKERR() directly !!
        cdef int ierr = MPI_Waitall(count, irequests, istatuses)
        tmp1 = restore_Request(requests, &irequests, count)
        tmp2 = restore_Status(statuses, &istatuses, count)
        CHKERR(ierr) # do error checking here
        #
        return None

    Waitall = classmethod(Waitall)

    ## @classmethod
    def Testall(cls, requests, statuses=None):
        """
        Test for completion of all previously initiated requests
        """
        cdef int count = len(requests)
        cdef MPI_Request *irequests = NULL
        cdef tmp1 = asarray_Request(requests, &irequests, count)
        cdef MPI_Status *istatuses = MPI_STATUSES_IGNORE
        cdef tmp2 = asarray_Status(statuses, &istatuses, count)
        cdef bint flag = 0
        # do not use CHKERR() directly !!
        cdef int ierr = MPI_Testall(count, irequests,
                                    &flag, istatuses)
        tmp1 = restore_Request(requests, &irequests, count)
        tmp2 = restore_Status(statuses, &istatuses, count)
        CHKERR(ierr) # do error checking here
        #
        return flag

    Testall = classmethod(Testall)

    ## @classmethod
    def Waitsome(cls, requests, statuses=None):
        """
        Wait for some previously initiated requests to complete
        """
        cdef int incount = len(requests)
        cdef MPI_Request *irequests = NULL
        cdef tmp1 = asarray_Request(requests, &irequests, incount)
        cdef MPI_Status *istatuses = MPI_STATUSES_IGNORE
        cdef tmp2 = asarray_Status(statuses, &istatuses, incount)
        cdef int outcount = MPI_UNDEFINED
        cdef int *iindices = NULL
        cdef tmp3 = newarray_int(incount, &iindices)
        # do not use CHKERR() directly !!
        cdef int ierr = MPI_Waitsome(incount, irequests,
                                     &outcount, iindices, istatuses)
        tmp1 = restore_Request(requests, &irequests, incount)
        tmp2 = restore_Status(statuses, &istatuses, incount)
        CHKERR(ierr) # do error checking here
        #
        cdef int i = 0
        indices = []
        if outcount != 0 and outcount != MPI_UNDEFINED:
            indices = [iindices[i] for i from 0 <= i < outcount]
        tmp3 = None
        return (outcount, indices)

    Waitsome = classmethod(Waitsome)

    ## @classmethod
    def Testsome(cls, requests, statuses=None):
        """
        Test for completion of some previously initiated requests
        """
        cdef int incount = len(requests)
        cdef MPI_Request *irequests = NULL
        cdef tmp1 = asarray_Request(requests, &irequests, incount)
        cdef MPI_Status *istatuses = MPI_STATUSES_IGNORE
        cdef tmp2 = asarray_Status(statuses, &istatuses, incount)
        cdef int outcount = MPI_UNDEFINED
        cdef int *iindices = NULL
        cdef tmp3 = newarray_int(incount, &iindices)
        # do not use CHKERR() directly !!
        cdef int ierr = MPI_Waitsome(incount, irequests,
                                     &outcount, iindices, istatuses)
        tmp1 = restore_Request(requests, &irequests, incount)
        tmp2 = restore_Status(statuses, &istatuses, incount)
        CHKERR(ierr) # do error checking here
        #
        cdef int i = 0
        indices = []
        if outcount != 0 and outcount != MPI_UNDEFINED:
            indices = [iindices[i] for i from 0 <= i < outcount]
        tmp3 = None
        return (outcount, indices)

    Testsome = classmethod(Testsome)

    # Cancel
    # ------

    def Cancel(self):
        """
        Cancel a communication request
        """
        CHKERR( MPI_Cancel(&self.ob_mpi) )



cdef class Prequest(Request):

    """
    Persistent request
    """

    def Start(self):
        """
        Initiate a communication with a persistent request
        """
        CHKERR( MPI_Start(&self.ob_mpi) )

    ## @classmethod
    def Startall(cls, requests):
        """
        Start a collection of persistent requests
        """
        cdef int count = len(requests)
        cdef MPI_Request *irequests = NULL
        cdef tmp = asarray_Request(requests, &irequests, count)
        # do not use CHKERR() directly !!
        cdef int ierr = MPI_Startall(count, irequests)
        tmp = restore_Request(requests, &irequests, count)
        CHKERR(ierr) # do error checking here

    Startall = classmethod(Startall)



cdef class Grequest(Request):

    """
    Generalized request
    """

    ## @classmethod
    def Start(cls, query_fn, free_fn, cancel_fn, extra_state):
        """
        Create and return a user-defined request
        """
        raise NotImplementedError # XXX implement!
        #
        cdef MPI_Grequest_query_function  *c_query_fn    = NULL
        cdef MPI_Grequest_free_function   *c_free_fn     = NULL
        cdef MPI_Grequest_cancel_function *c_cancel_fn   = NULL
        cdef void                         *c_extra_state = NULL
        #
        cdef Grequest request = cls()
        CHKERR( MPI_Grequest_start(c_query_fn, c_free_fn, c_cancel_fn,
                                   c_extra_state, &request.ob_mpi) )

    Start = classmethod(Start)

    def Complete(self):
        """
        Notify that a user-defined request is complete
        """
        CHKERR( MPI_Grequest_complete(self.ob_mpi) )


# Null request handle
# -------------------

REQUEST_NULL = _new_Request(MPI_REQUEST_NULL)
