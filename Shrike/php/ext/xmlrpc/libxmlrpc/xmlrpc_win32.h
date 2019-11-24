#ifndef _XMLRPC_WIN32_H
#define _XMLRPC_WIN32_H
/* just some things needed to compile win32 */
#include <windows.h>
#include <stdlib.h>
#ifndef inline
# define inline __inline
#endif
#if !defined(snprintf) && _MSC_VER < 1900
# define snprintf _snprintf
#endif
#ifndef strcasecmp
# define strcasecmp(s1, s2) stricmp(s1, s2)
#endif

#endif
