/* $Id$ */

#ifndef PyMPI_COMPAT_MPICH1_H
#define PyMPI_COMPAT_MPICH1_H

#if defined(MPICH_NAME) && MPICH_NAME==1

/* ---------------------------------------------------------------- */

#ifndef Py_PYTHON_H
#error "this header requires <Python.h> included"
#endif

/* this does not actually work in parallel, */
/* but avoids a nasty segfault.             */

static int    PyMPI_MPICH1_argc    = 0;
static char **PyMPI_MPICH1_argv    = 0;
static char  *PyMPI_MPICH1_args[2] = {0, 0};

static int PyMPI_MPICH1_MPI_Init(int *argc, char ***argv)
{
  if (argc==(int *)0 || argv==(char ***)0) {
    PyMPI_MPICH1_args[0] = Py_GetProgramName();
    PyMPI_MPICH1_argc = 1;
    PyMPI_MPICH1_argv = PyMPI_MPICH1_args;
    argc = &PyMPI_MPICH1_argc;
    argv = &PyMPI_MPICH1_argv;
  }
  return MPI_Init(argc, argv);
}
#undef  MPI_Init
#define MPI_Init PyMPI_MPICH1_MPI_Init

static int PyMPI_MPICH1_MPI_Init_thread(int *argc, char ***argv,
					int required, int *provided)
{
  if (argc==(int *)0 || argv==(char ***)0) {
    PyMPI_MPICH1_args[0] = Py_GetProgramName();
    PyMPI_MPICH1_argc = 1;
    PyMPI_MPICH1_argv = PyMPI_MPICH1_args;
    argc = &PyMPI_MPICH1_argc;
    argv = &PyMPI_MPICH1_argv;
  }
  return MPI_Init_thread(argc, argv, required, provided);
}
#undef  MPI_Init_thread
#define MPI_Init_thread PyMPI_MPICH1_MPI_Init_thread

/* ---------------------------------------------------------------- */

static int PyMPI_MPICH1_MPI_Status_set_elements(MPI_Status *status,
						MPI_Datatype datatype,
						int count)
{
  if (datatype == MPI_DATATYPE_NULL) return MPI_ERR_TYPE;
  return MPI_Status_set_elements(status, datatype, count);
}
#undef  MPI_Status_set_elements
#define MPI_Status_set_elements PyMPI_MPICH1_MPI_Status_set_elements

/* ---------------------------------------------------------------- */

static int PyMPI_MPICH1_MPI_Sendrecv(void *sendbuf, 
				     int sendcount, 
				     MPI_Datatype sendtype,
				     int dest, 
				     int sendtag,
				     void *recvbuf, 
				     int recvcount, 
				     MPI_Datatype recvtype,
				     int source, 
				     int recvtag,
				     MPI_Comm comm, 
				     MPI_Status *status)
{
  MPI_Status dummy;
  if (status == MPI_STATUS_IGNORE) status = &dummy;
  return MPI_Sendrecv(sendbuf, sendcount, sendtype, dest,   sendtag,
		      recvbuf, recvcount, recvtype, source, recvtag,
		      comm, status);
}
#undef  MPI_Sendrecv
#define MPI_Sendrecv PyMPI_MPICH1_MPI_Sendrecv

/* ---------------------------------------------------------------- */

#if defined(ROMIO) && ROMIO==1
#if defined(MPIO_INCLUDE)

#if defined(__cplusplus)
extern "C" {
#endif

#define MPIR_COOKIE unsigned long cookie;
struct MPIR_Errhandler {
  MPIR_COOKIE
  MPI_Handler_function *routine;
  int                  ref_count;
};
void *MPIR_ToPointer(int);

#if defined(__cplusplus)
}
#endif

static int PyMPI_MPICH1_MPI_File_get_errhandler(MPI_File file, 
						MPI_Errhandler *errhandler)
{
  int ierr = MPI_SUCCESS;
  ierr = MPI_File_get_errhandler(file, errhandler);
  if (ierr != MPI_SUCCESS) return ierr;
  if (errhandler == 0) return ierr; /* just in case  */
  /* manage reference counting */
  if (*errhandler != MPI_ERRHANDLER_NULL) {
    struct MPIR_Errhandler *eh = 
      (struct MPIR_Errhandler *) MPIR_ToPointer(*errhandler);
    if (eh) eh->ref_count++;
  }
  return MPI_SUCCESS;
}

static int PyMPI_MPICH1_MPI_File_set_errhandler(MPI_File file, 
						MPI_Errhandler errhandler)
{
  int ierr = MPI_SUCCESS;
  MPI_Errhandler previous = MPI_ERRHANDLER_NULL;
  ierr = MPI_File_get_errhandler(file, &previous);
  if (ierr != MPI_SUCCESS) return ierr;
  ierr = MPI_File_set_errhandler(file, errhandler);
  if (ierr != MPI_SUCCESS) return ierr;
  /* manage reference counting */
  if (previous != MPI_ERRHANDLER_NULL) {
    struct MPIR_Errhandler *eh = 
      (struct MPIR_Errhandler *) MPIR_ToPointer(previous);
    if (eh) eh->ref_count--;
  }
  if (errhandler != MPI_ERRHANDLER_NULL) {
    struct MPIR_Errhandler *eh = 
      (struct MPIR_Errhandler *) MPIR_ToPointer(errhandler);
    if (eh) eh->ref_count++;
  }
  return MPI_SUCCESS;
}

#undef  MPI_File_get_errhandler
#define MPI_File_get_errhandler PyMPI_MPICH1_MPI_File_get_errhandler

#undef  MPI_File_set_errhandler
#define MPI_File_set_errhandler PyMPI_MPICH1_MPI_File_set_errhandler

#endif /* !ROMIO==1 */
#endif /* !MPIO_INCLUDE */

/* ---------------------------------------------------------------- */

#undef  MPI_MAX_OBJECT_NAME
#define MPI_MAX_OBJECT_NAME MPI_MAX_NAME_STRING

/* ---------------------------------------------------------------- */

#endif /* !MPICH_NAME==1 */

#endif /* !PyMPI_COMPAT_MPICH1_H */