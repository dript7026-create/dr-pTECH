#ifndef DOTXT_FILE_IO_H
#define DOTXT_FILE_IO_H

#include <stdbool.h>
#include <windows.h>

bool dotxt_load_into_editor(HWND hwndEdit, const wchar_t* path);
bool dotxt_save_from_editor(HWND hwndEdit, const wchar_t* path);

#endif
