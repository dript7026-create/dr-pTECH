/* stb_image_impl.c — Compile unit for stb_image
 * Downloads and defines the implementation.
 * Since stb_image.h is a single-header library, this file defines the
 * implementation once. Other files include stb_image.h without the define.
 *
 * To obtain stb_image.h, run:
 *   curl -L -o viewer/stb_image.h https://raw.githubusercontent.com/nothings/stb/master/stb_image.h
 *
 * Or use the build script which downloads it automatically.
 */
#define STB_IMAGE_IMPLEMENTATION
#ifdef __has_include
  #if __has_include("stb_image.h")
    #include "stb_image.h"
  #endif
#else
  #include "stb_image.h"
#endif
