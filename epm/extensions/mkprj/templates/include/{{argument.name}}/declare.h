{% set name = argument.name %}
{% set version = argument.version %}
{% set id = name.replace('-', '_') %}
{% set ID = name.upper() %}
#ifndef _{{ID}}_LIBRARY_DECLARATION_HEADER_H_
#define _{{ID}}_LIBRARY_DECLARATION_HEADER_H_


#if defined(_MSC_VER)
    #if defined({{ name | upper }}_USE_DLLS)
        #ifdef {{ name | upper }}_EXPORTS
            #define {{ ID }}_EXPORT_ATTRIBUTE __declspec(dllexport)
        #else
            #define {{ ID }}_EXPORT_ATTRIBUTE __declspec(dllimport)
        #endif
    #else
        #define {{ ID }}_EXPORT_ATTRIBUTE
    #endif
#else
    #ifndef {{ ID }}_EXPORT_ATTRIBUTE
        #define {{ ID }}_EXPORT_ATTRIBUTE
    #endif
#endif


/* explict C API  interface declaration macro */
#ifndef {{ ID }}_C_EXPORT
	#ifdef __cplusplus
        #define  {{ ID }}_C_EXPORT extern "C" {{ ID }}_EXPORT_ATTRIBUTE
	#else
	    #define  {{ ID }}_C_EXPORT {{ ID }}_EXPORT_ATTRIBUTE
	#endif
#endif

/* C/C++ API  interface declaration macro */
#ifndef {{ ID }}_EXPORT
    #define {{ ID }}_EXPORT {{ ID }}_EXPORT_ATTRIBUTE
#endif

#define {{ID}}_API {{ID}}_EXPORT
#define {{ID}}_C_API {{ID}}_C_EXPORT

/* deprecated info on compiler*/
#if defined(__GNUC__) && ((__GNUC__ >= 4) || ((__GNUC__ == 3) && (__GNUC_MINOR__ >= 1)))

    #define {{ ID }}_DEPRECATED __attribute__((deprecated))
    #define {{ ID }}_DEPRECATED_TEXT(text) __attribute__((deprecated))

#elif _MSC_VER >= 1400 //vs 2005 or higher
    #define {{ ID }}_DEPRECATED __declspec(deprecated)
    #define {{ ID }}_DEPRECATED_TEXT(text) __declspec(deprecated(text))

#else
    #define {{ ID }}_DEPRECATED
#endif


#endif /* !_{{ID}}_EXPORT_LIBRARY_DECLARATION_HEADER_H_ */