/*
   +----------------------------------------------------------------------+
   | PHP Version 7                                                        |
   +----------------------------------------------------------------------+
   | Copyright (c) 1997-2017 The PHP Group                                |
   +----------------------------------------------------------------------+
   | This source file is subject to version 3.01 of the PHP license,      |
   | that is bundled with this package in the file LICENSE, and is        |
   | available through the world-wide-web at the following url:           |
   | http://www.php.net/license/3_01.txt                                  |
   | If you did not receive a copy of the PHP license and are unable to   |
   | obtain it through the world-wide-web, please send a note to          |
   | license@php.net so we can mail you a copy immediately.               |
   +----------------------------------------------------------------------+
   | Author: Zeev Suraski <zeev@zend.com>                                 |
   *         Pierre Joye <pierre@php.net>                                 |
   +----------------------------------------------------------------------+
 */

/* $Id$ */

#include "php.h"
#include "winutil.h"
#include <wincrypt.h>
#include <lmcons.h>

PHP_WINUTIL_API char *php_win32_error_to_msg(HRESULT error)
{
	char *buf = NULL;

	FormatMessage(
		FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |	FORMAT_MESSAGE_IGNORE_INSERTS,
		NULL, error, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),	(LPTSTR)&buf, 0, NULL
	);

	return (buf ? (char *) buf : "");
}

int php_win32_check_trailing_space(const char * path, const int path_len) {
	if (path_len < 1) {
		return 1;
	}
	if (path) {
		if (path[0] == ' ' || path[path_len - 1] == ' ') {
			return 0;
		} else {
			return 1;
		}
	} else {
		return 0;
	}
}

HCRYPTPROV   hCryptProv;
unsigned int has_crypto_ctx = 0;

#ifdef ZTS
MUTEX_T php_lock_win32_cryptoctx;
void php_win32_init_rng_lock()
{
	php_lock_win32_cryptoctx = tsrm_mutex_alloc();
}

void php_win32_free_rng_lock()
{
	tsrm_mutex_lock(php_lock_win32_cryptoctx);
	if (has_crypto_ctx == 1) {
		CryptReleaseContext(hCryptProv, 0);
		has_crypto_ctx = 0;
	}
	tsrm_mutex_unlock(php_lock_win32_cryptoctx);
	tsrm_mutex_free(php_lock_win32_cryptoctx);

}
#else
#define php_win32_init_rng_lock();
#define php_win32_free_rng_lock();
#endif



PHP_WINUTIL_API int php_win32_get_random_bytes(unsigned char *buf, size_t size) {  /* {{{ */

	BOOL ret;

#ifdef ZTS
	tsrm_mutex_lock(php_lock_win32_cryptoctx);
#endif

	if (has_crypto_ctx == 0) {
		/* CRYPT_VERIFYCONTEXT > only hashing&co-like use, no need to acces prv keys */
		if (!CryptAcquireContext(&hCryptProv, NULL, NULL, PROV_RSA_FULL, CRYPT_MACHINE_KEYSET|CRYPT_VERIFYCONTEXT )) {
			/* Could mean that the key container does not exist, let try
			   again by asking for a new one. If it fails here, it surely means that the user running
               this process does not have the permission(s) to use this container.
             */
			if (GetLastError() == NTE_BAD_KEYSET) {
				if (CryptAcquireContext(&hCryptProv, NULL, NULL, PROV_RSA_FULL, CRYPT_NEWKEYSET | CRYPT_MACHINE_KEYSET | CRYPT_VERIFYCONTEXT )) {
					has_crypto_ctx = 1;
				} else {
					has_crypto_ctx = 0;
				}
			}
		} else {
			has_crypto_ctx = 1;
		}
	}

#ifdef ZTS
	tsrm_mutex_unlock(php_lock_win32_cryptoctx);
#endif

	if (has_crypto_ctx == 0) {
		return FAILURE;
	}

	/* XXX should go in the loop if size exceeds UINT_MAX */
	ret = CryptGenRandom(hCryptProv, (DWORD)size, buf);

	if (ret) {
		return SUCCESS;
	} else {
		return FAILURE;
	}
}
/* }}} */


/*
* This functions based on the code from the UNIXem project under
* the BSD like license. Modified for PHP by ab@php.net
*
* Home:    http://synesis.com.au/software/
*
* Copyright (c) 2005-2010, Matthew Wilson and Synesis Software
*/

PHP_WINUTIL_API int php_win32_code_to_errno(unsigned long w32Err)
{
    size_t  i;

    struct code_to_errno_map
    {
        unsigned long   w32Err;
        int             eerrno;
    };

    static const struct code_to_errno_map errmap[] = 
    {
        /*   1 */       {   ERROR_INVALID_FUNCTION          ,   EINVAL          }
        /*   2 */   ,   {   ERROR_FILE_NOT_FOUND            ,   ENOENT          }
        /*   3 */   ,   {   ERROR_PATH_NOT_FOUND            ,   ENOENT          }
        /*   4 */   ,   {   ERROR_TOO_MANY_OPEN_FILES       ,   EMFILE          }
        /*   5 */   ,   {   ERROR_ACCESS_DENIED             ,   EACCES          }
        /*   6 */   ,   {   ERROR_INVALID_HANDLE            ,   EBADF           }
        /*   7 */   ,   {   ERROR_ARENA_TRASHED             ,   ENOMEM          }
        /*   8 */   ,   {   ERROR_NOT_ENOUGH_MEMORY         ,   ENOMEM          }
        /*   9 */   ,   {   ERROR_INVALID_BLOCK             ,   ENOMEM          }
        /*  10 */   ,   {   ERROR_BAD_ENVIRONMENT           ,   E2BIG           }
        /*  11 */   ,   {   ERROR_BAD_FORMAT                ,   ENOEXEC         }
        /*  12 */   ,   {   ERROR_INVALID_ACCESS            ,   EINVAL          }
        /*  13 */   ,   {   ERROR_INVALID_DATA              ,   EINVAL          }
        /*  14 */   ,   {   ERROR_OUTOFMEMORY               ,   ENOMEM          }
        /*  15 */   ,   {   ERROR_INVALID_DRIVE             ,   ENOENT          }
        /*  16 */   ,   {   ERROR_CURRENT_DIRECTORY         ,   ECURDIR         }
        /*  17 */   ,   {   ERROR_NOT_SAME_DEVICE           ,   EXDEV           }
        /*  18 */   ,   {   ERROR_NO_MORE_FILES             ,   ENOENT          }
        /*  19 */   ,   {   ERROR_WRITE_PROTECT             ,   EROFS           }
        /*  20 */   ,   {   ERROR_BAD_UNIT                  ,   ENXIO           }
        /*  21 */   ,   {   ERROR_NOT_READY                 ,   EBUSY           }
        /*  22 */   ,   {   ERROR_BAD_COMMAND               ,   EIO             }
        /*  23 */   ,   {   ERROR_CRC                       ,   EIO             }
        /*  24 */   ,   {   ERROR_BAD_LENGTH                ,   EIO             }
        /*  25 */   ,   {   ERROR_SEEK                      ,   EIO             }
        /*  26 */   ,   {   ERROR_NOT_DOS_DISK              ,   EIO             }
        /*  27 */   ,   {   ERROR_SECTOR_NOT_FOUND          ,   ENXIO           }
        /*  28 */   ,   {   ERROR_OUT_OF_PAPER              ,   EBUSY           }
        /*  29 */   ,   {   ERROR_WRITE_FAULT               ,   EIO             }
        /*  30 */   ,   {   ERROR_READ_FAULT                ,   EIO             }
        /*  31 */   ,   {   ERROR_GEN_FAILURE               ,   EIO             }
        /*  32 */   ,   {   ERROR_SHARING_VIOLATION         ,   EAGAIN          }
        /*  33 */   ,   {   ERROR_LOCK_VIOLATION            ,   EACCES          }
        /*  34 */   ,   {   ERROR_WRONG_DISK                ,   ENXIO           }
        /*  35 */   ,   {   35                              ,   ENFILE          }
        /*  36 */   ,   {   ERROR_SHARING_BUFFER_EXCEEDED   ,   ENFILE          }
        /*  37 */   ,   {   ERROR_HANDLE_EOF                ,   EINVAL          }
        /*  38 */   ,   {   ERROR_HANDLE_DISK_FULL          ,   ENOSPC          }
#if 0
        /*  39 */   ,   {   0                               ,   0               }
        /*  40 */   ,   {   0                               ,   0               }
        /*  41 */   ,   {   0                               ,   0               }
        /*  42 */   ,   {   0                               ,   0               }
        /*  43 */   ,   {   0                               ,   0               }
        /*  44 */   ,   {   0                               ,   0               }
        /*  45 */   ,   {   0                               ,   0               }
        /*  46 */   ,   {   0                               ,   0               }
        /*  47 */   ,   {   0                               ,   0               }
        /*  48 */   ,   {   0                               ,   0               }
        /*  49 */   ,   {   0                               ,   0               }
#endif
        /*  50 */   ,   {   ERROR_NOT_SUPPORTED             ,   ENOSYS          }
#if 0
        /*  51 */   ,   {   0                               ,   0               }
        /*  52 */   ,   {   0                               ,   0               }
#endif
        /*  53 */   ,   {   ERROR_BAD_NETPATH               ,   ENOENT          }
#if 0
        /*  54 */   ,   {   0                               ,   0               }
        /*  55 */   ,   {   0                               ,   0               }
        /*  56 */   ,   {   0                               ,   0               }
        /*  57 */   ,   {   0                               ,   0               }
        /*  58 */   ,   {   0                               ,   0               }
        /*  59 */   ,   {   0                               ,   0               }
        /*  60 */   ,   {   0                               ,   0               }
        /*  61 */   ,   {   0                               ,   0               }
        /*  62 */   ,   {   0                               ,   0               }
        /*  63 */   ,   {   0                               ,   0               }
        /*  64 */   ,   {   0                               ,   0               }
#endif
        /*  65 */   ,   {   ERROR_NETWORK_ACCESS_DENIED     ,   EACCES          }
#if 0
        /*  66 */   ,   {   0                               ,   0               }
#endif
        /*  67 */   ,   {   ERROR_BAD_NET_NAME              ,   ENOENT          }
#if 0
        /*  68 */   ,   {   0                               ,   0               }
        /*  69 */   ,   {   0                               ,   0               }
        /*  70 */   ,   {   0                               ,   0               }
        /*  71 */   ,   {   0                               ,   0               }
        /*  72 */   ,   {   0                               ,   0               }
        /*  73 */   ,   {   0                               ,   0               }
        /*  74 */   ,   {   0                               ,   0               }
        /*  75 */   ,   {   0                               ,   0               }
        /*  76 */   ,   {   0                               ,   0               }
        /*  77 */   ,   {   0                               ,   0               }
        /*  78 */   ,   {   0                               ,   0               }
        /*  79 */   ,   {   0                               ,   0               }
#endif
        /*  80 */   ,   {   ERROR_FILE_EXISTS               ,   EEXIST          }
#if 0
        /*  81 */   ,   {   0                               ,   0               }
#endif
        /*  82 */   ,   {   ERROR_CANNOT_MAKE               ,   EACCES          }
        /*  83 */   ,   {   ERROR_FAIL_I24                  ,   EACCES          }
#if 0
        /*  84 */   ,   {   0                               ,   0               }
        /*  85 */   ,   {   0                               ,   0               }
        /*  86 */   ,   {   0                               ,   0               }
#endif
        /*  87 */   ,   {   ERROR_INVALID_PARAMETER         ,   EINVAL          }
#if 0
        /*  88 */   ,   {   0                               ,   0               }
#endif
        /*  89 */   ,   {   ERROR_NO_PROC_SLOTS             ,   EAGAIN          }
#if 0
        /*  90 */   ,   {   0                               ,   0               }
        /*  91 */   ,   {   0                               ,   0               }
        /*  92 */   ,   {   0                               ,   0               }
        /*  93 */   ,   {   0                               ,   0               }
        /*  94 */   ,   {   0                               ,   0               }
        /*  95 */   ,   {   0                               ,   0               }
        /*  96 */   ,   {   0                               ,   0               }
        /*  97 */   ,   {   0                               ,   0               }
        /*  98 */   ,   {   0                               ,   0               }
        /*  99 */   ,   {   0                               ,   0               }
        /* 100 */   ,   {   0                               ,   0               }
        /* 101 */   ,   {   0                               ,   0               }
        /* 102 */   ,   {   0                               ,   0               }
        /* 103 */   ,   {   0                               ,   0               }
        /* 104 */   ,   {   0                               ,   0               }
        /* 105 */   ,   {   0                               ,   0               }
        /* 106 */   ,   {   0                               ,   0               }
        /* 107 */   ,   {   0                               ,   0               }
#endif
        /* 108 */   ,   {   ERROR_DRIVE_LOCKED              ,   EACCES          }
        /* 109 */   ,   {   ERROR_BROKEN_PIPE               ,   EPIPE           }
#if 0
        /* 110 */   ,   {   0                               ,   0               }
#endif
        /* 111 */   ,   {   ERROR_BUFFER_OVERFLOW           ,   ENAMETOOLONG    }
        /* 112 */   ,   {   ERROR_DISK_FULL                 ,   ENOSPC          }
#if 0
        /* 113 */   ,   {   0                               ,   0               }
#endif
        /* 114 */   ,   {   ERROR_INVALID_TARGET_HANDLE     ,   EBADF           }
#if 0
        /* 115 */   ,   {   0                               ,   0               }
        /* 116 */   ,   {   0                               ,   0               }
        /* 117 */   ,   {   0                               ,   0               }
        /* 118 */   ,   {   0                               ,   0               }
        /* 119 */   ,   {   0                               ,   0               }
        /* 120 */   ,   {   0                               ,   0               }
        /* 121 */   ,   {   0                               ,   0               }
#endif
        /* 122 */   ,   {   ERROR_INSUFFICIENT_BUFFER       ,   ERANGE          }
        /* 123 */   ,   {   ERROR_INVALID_NAME              ,   ENOENT          }
        /* 124 */   ,   {   ERROR_INVALID_HANDLE            ,   EINVAL          }
#if 0
        /* 125 */   ,   {   0                               ,   0               }
#endif
        /* 126 */   ,   {   ERROR_MOD_NOT_FOUND             ,   ENOENT          }
        /* 127 */   ,   {   ERROR_PROC_NOT_FOUND            ,   ENOENT          }
        /* 128 */   ,   {   ERROR_WAIT_NO_CHILDREN          ,   ECHILD          }
        /* 129 */   ,   {   ERROR_CHILD_NOT_COMPLETE        ,   ECHILD          }
        /* 130 */   ,   {   ERROR_DIRECT_ACCESS_HANDLE      ,   EBADF           }
        /* 131 */   ,   {   ERROR_NEGATIVE_SEEK             ,   EINVAL          }
        /* 132 */   ,   {   ERROR_SEEK_ON_DEVICE            ,   EACCES          }
#if 0
        /* 133 */   ,   {   0                               ,   0               }
        /* 134 */   ,   {   0                               ,   0               }
        /* 135 */   ,   {   0                               ,   0               }
        /* 136 */   ,   {   0                               ,   0               }
        /* 137 */   ,   {   0                               ,   0               }
        /* 138 */   ,   {   0                               ,   0               }
        /* 139 */   ,   {   0                               ,   0               }
        /* 140 */   ,   {   0                               ,   0               }
        /* 141 */   ,   {   0                               ,   0               }
        /* 142 */   ,   {   0                               ,   0               }
        /* 143 */   ,   {   0                               ,   0               }
        /* 144 */   ,   {   0                               ,   0               }
#endif
        /* 145 */   ,   {   ERROR_DIR_NOT_EMPTY             ,   ENOTEMPTY       }
#if 0
        /* 146 */   ,   {   0                               ,   0               }
        /* 147 */   ,   {   0                               ,   0               }
        /* 148 */   ,   {   0                               ,   0               }
        /* 149 */   ,   {   0                               ,   0               }
        /* 150 */   ,   {   0                               ,   0               }
        /* 151 */   ,   {   0                               ,   0               }
        /* 152 */   ,   {   0                               ,   0               }
        /* 153 */   ,   {   0                               ,   0               }
        /* 154 */   ,   {   0                               ,   0               }
        /* 155 */   ,   {   0                               ,   0               }
        /* 156 */   ,   {   0                               ,   0               }
        /* 157 */   ,   {   0                               ,   0               }
#endif
        /* 158 */   ,   {   ERROR_NOT_LOCKED                ,   EACCES          }
#if 0
        /* 159 */   ,   {   0                               ,   0               }
        /* 160 */   ,   {   0                               ,   0               }
#endif
        /* 161 */   ,   {   ERROR_BAD_PATHNAME              ,   ENOENT          }
#if 0
        /* 162 */   ,   {   0                               ,   0               }
        /* 163 */   ,   {   0                               ,   0               }
#endif
        /* 164 */   ,   {   ERROR_MAX_THRDS_REACHED         ,   EAGAIN          }
#if 0
        /* 165 */   ,   {   0                               ,   0               }
        /* 166 */   ,   {   0                               ,   0               }
#endif
        /* 167 */   ,   {   ERROR_LOCK_FAILED               ,   EACCES          }
#if 0
        /* 168 */   ,   {   0                               ,   0               }
        /* 169 */   ,   {   0                               ,   0               }
        /* 170 */   ,   {   0                               ,   0               }
        /* 171 */   ,   {   0                               ,   0               }
        /* 172 */   ,   {   0                               ,   0               }
        /* 173 */   ,   {   0                               ,   0               }
        /* 174 */   ,   {   0                               ,   0               }
        /* 175 */   ,   {   0                               ,   0               }
        /* 176 */   ,   {   0                               ,   0               }
        /* 177 */   ,   {   0                               ,   0               }
        /* 178 */   ,   {   0                               ,   0               }
        /* 179 */   ,   {   0                               ,   0               }
        /* 180 */   ,   {   0                               ,   0               }
        /* 181 */   ,   {   0                               ,   0               }
        /* 182 */   ,   {   0                               ,   0               }
#endif
        /* 183 */   ,   {   ERROR_ALREADY_EXISTS            ,   EEXIST          }
#if 0
        /* 184 */   ,   {   0                               ,   0               }
        /* 185 */   ,   {   0                               ,   0               }
        /* 186 */   ,   {   0                               ,   0               }
        /* 187 */   ,   {   0                               ,   0               }
        /* 188 */   ,   {   0                               ,   0               }
        /* 189 */   ,   {   0                               ,   0               }
        /* 190 */   ,   {   0                               ,   0               }
        /* 191 */   ,   {   0                               ,   0               }
        /* 192 */   ,   {   0                               ,   0               }
        /* 193 */   ,   {   0                               ,   0               }
        /* 194 */   ,   {   0                               ,   0               }
        /* 195 */   ,   {   0                               ,   0               }
        /* 196 */   ,   {   0                               ,   0               }
        /* 197 */   ,   {   0                               ,   0               }
        /* 198 */   ,   {   0                               ,   0               }
        /* 199 */   ,   {   0                               ,   0               }
#endif

        /* 206 */   ,   {   ERROR_FILENAME_EXCED_RANGE      ,   ENAMETOOLONG    }

        /* 215 */   ,   {   ERROR_NESTING_NOT_ALLOWED       ,   EAGAIN          }
		/* 258 */   ,   { WAIT_TIMEOUT, ETIME}

        /* 267 */   ,   {   ERROR_DIRECTORY                 ,   ENOTDIR         }

        /* 996 */   ,   {   ERROR_IO_INCOMPLETE             ,   EAGAIN          }
        /* 997 */   ,   {   ERROR_IO_PENDING                ,   EAGAIN          }

        /* 1004 */   ,  {   ERROR_INVALID_FLAGS             ,   EINVAL          }
        /* 1113 */   ,  {   ERROR_NO_UNICODE_TRANSLATION    ,   EINVAL          }
        /* 1168 */   ,  {   ERROR_NOT_FOUND                 ,   ENOENT          }
        /* 1224 */   ,  {   ERROR_USER_MAPPED_FILE          ,   EACCES          }
        /* 1816 */  ,   {   ERROR_NOT_ENOUGH_QUOTA          ,   ENOMEM          }
					,   {   ERROR_ABANDONED_WAIT_0          ,   EIO }
    };

    for(i = 0; i < sizeof(errmap)/sizeof(struct code_to_errno_map); ++i)
    {
        if(w32Err == errmap[i].w32Err)
        {
            return errmap[i].eerrno;
        }
    }

    assert(!"Unrecognised value");

    return EINVAL;
}

PHP_WINUTIL_API char *php_win32_get_username(void)
{
	wchar_t unamew[UNLEN + 1];
	size_t uname_len;
	char *uname;
	DWORD unsize = UNLEN;

	GetUserNameW(unamew, &unsize);
	uname = php_win32_cp_conv_w_to_any(unamew, unsize - 1, &uname_len);
	if (!uname) {
		return NULL;
	}

	/* Ensure the length doesn't overflow. */
	if (uname_len > UNLEN) {
		uname[uname_len] = '\0';
	}

	return uname;
}

/*
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * End:
 * vim600: sw=4 ts=4 fdm=marker
 * vim<600: sw=4 ts=4
 */
