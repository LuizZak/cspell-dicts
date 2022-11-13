#define wchar_t short
#define _WCHAR_T_DEFINED
#define __int8 int
#define __int16 int
#define __int32 int
#define __int64 int
#define __cdecl
#define __pragma(x)
#define __inline
#define __forceinline
#define __ptr32
#define __ptr64
#define __unaligned
#define __stdcall
#define _stdcall
#define __alignof(x) 1
#define __declspec(x)
#define _declspec(x)

#define UNICODE

// Common name for precompiled header files on Windows (see https://stackoverflow.com/a/4726838)
typedef void* stdafx;

// Need to disable a few declarations used by SAL-compliant code on the following imports
#define __in
#define __out
#define __inout
#define __in_opt
#define __out_opt
#define __inout_opt
#define __in_ecount(x)
#define __in_ecount_opt(x)
#define __in_bcount(x)

/// Work around GCC-specific features
#define __builtin_va_list void

#define __restrict
#define __attribute__(va)
#define __asm__(x)

#include "temp/z3/src/api/z3.h"
