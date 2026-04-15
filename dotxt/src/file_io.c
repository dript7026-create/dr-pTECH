#include "file_io.h"

#include <Richedit.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

static bool has_extension(const wchar_t* path, const wchar_t* ext) {
    const wchar_t* dot = wcsrchr(path, L'.');
    if (!dot) {
        return false;
    }
    return _wcsicmp(dot, ext) == 0;
}

typedef struct StreamIoCtx {
    HANDLE file;
} StreamIoCtx;

static DWORD CALLBACK editstream_in_cb(DWORD_PTR cookie, LPBYTE pbBuff, LONG cb, LONG* pcb) {
    StreamIoCtx* ctx = (StreamIoCtx*)cookie;
    DWORD readBytes = 0;
    if (!ReadFile(ctx->file, pbBuff, (DWORD)cb, &readBytes, NULL)) {
        return 1;
    }
    *pcb = (LONG)readBytes;
    return 0;
}

static DWORD CALLBACK editstream_out_cb(DWORD_PTR cookie, LPBYTE pbBuff, LONG cb, LONG* pcb) {
    StreamIoCtx* ctx = (StreamIoCtx*)cookie;
    DWORD wroteBytes = 0;
    if (!WriteFile(ctx->file, pbBuff, (DWORD)cb, &wroteBytes, NULL)) {
        return 1;
    }
    *pcb = (LONG)wroteBytes;
    return 0;
}

static bool load_rtf(HWND hwndEdit, const wchar_t* path) {
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }

    StreamIoCtx ctx = { file };
    EDITSTREAM es;
    es.dwCookie = (DWORD_PTR)&ctx;
    es.dwError = 0;
    es.pfnCallback = editstream_in_cb;

    LRESULT ok = SendMessageW(hwndEdit, EM_STREAMIN, SF_RTF, (LPARAM)&es);
    CloseHandle(file);

    return ok != 0 && es.dwError == 0;
}

static bool save_rtf(HWND hwndEdit, const wchar_t* path) {
    HANDLE file = CreateFileW(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        return false;
    }

    StreamIoCtx ctx = { file };
    EDITSTREAM es;
    es.dwCookie = (DWORD_PTR)&ctx;
    es.dwError = 0;
    es.pfnCallback = editstream_out_cb;

    LRESULT ok = SendMessageW(hwndEdit, EM_STREAMOUT, SF_RTF, (LPARAM)&es);
    CloseHandle(file);

    return ok != 0 && es.dwError == 0;
}

static BYTE* read_all_bytes(const wchar_t* path, DWORD* outSize) {
    HANDLE file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        return NULL;
    }

    LARGE_INTEGER size;
    if (!GetFileSizeEx(file, &size) || size.QuadPart < 0 || size.QuadPart > 0x7fffffff) {
        CloseHandle(file);
        return NULL;
    }

    DWORD bytesToRead = (DWORD)size.QuadPart;
    BYTE* data = (BYTE*)malloc(bytesToRead + 1);
    if (!data) {
        CloseHandle(file);
        return NULL;
    }

    DWORD bytesRead = 0;
    bool ok = ReadFile(file, data, bytesToRead, &bytesRead, NULL) && bytesRead == bytesToRead;
    CloseHandle(file);

    if (!ok) {
        free(data);
        return NULL;
    }

    data[bytesToRead] = 0;
    *outSize = bytesToRead;
    return data;
}

static wchar_t* decode_text_to_utf16(const BYTE* data, DWORD size) {
    if (size >= 2 && data[0] == 0xFF && data[1] == 0xFE) {
        DWORD charCount = (size - 2) / 2;
        wchar_t* out = (wchar_t*)malloc((charCount + 1) * sizeof(wchar_t));
        if (!out) {
            return NULL;
        }
        memcpy(out, data + 2, charCount * sizeof(wchar_t));
        out[charCount] = 0;
        return out;
    }

    if (size >= 2 && data[0] == 0xFE && data[1] == 0xFF) {
        DWORD u16Count = (size - 2) / 2;
        wchar_t* out = (wchar_t*)malloc((u16Count + 1) * sizeof(wchar_t));
        if (!out) {
            return NULL;
        }
        for (DWORD i = 0; i < u16Count; ++i) {
            BYTE hi = data[2 + (i * 2)];
            BYTE lo = data[2 + (i * 2) + 1];
            out[i] = (wchar_t)(((unsigned short)hi << 8) | lo);
        }
        out[u16Count] = 0;
        return out;
    }

    const char* textPtr = (const char*)data;
    int textLen = (int)size;

    if (size >= 3 && data[0] == 0xEF && data[1] == 0xBB && data[2] == 0xBF) {
        textPtr += 3;
        textLen -= 3;
    }

    int needed = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, textPtr, textLen, NULL, 0);
    if (needed > 0) {
        wchar_t* out = (wchar_t*)malloc((needed + 1) * sizeof(wchar_t));
        if (!out) {
            return NULL;
        }
        MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, textPtr, textLen, out, needed);
        out[needed] = 0;
        return out;
    }

    needed = MultiByteToWideChar(CP_ACP, 0, textPtr, textLen, NULL, 0);
    if (needed <= 0) {
        return NULL;
    }

    wchar_t* out = (wchar_t*)malloc((needed + 1) * sizeof(wchar_t));
    if (!out) {
        return NULL;
    }

    MultiByteToWideChar(CP_ACP, 0, textPtr, textLen, out, needed);
    out[needed] = 0;
    return out;
}

static bool save_utf8_text(HWND hwndEdit, const wchar_t* path) {
    int chars = GetWindowTextLengthW(hwndEdit);
    wchar_t* bufferW = (wchar_t*)malloc((chars + 1) * sizeof(wchar_t));
    if (!bufferW) {
        return false;
    }

    GetWindowTextW(hwndEdit, bufferW, chars + 1);

    int utf8Bytes = WideCharToMultiByte(CP_UTF8, 0, bufferW, chars, NULL, 0, NULL, NULL);
    if (utf8Bytes < 0) {
        free(bufferW);
        return false;
    }

    char* bufferU8 = NULL;
    if (utf8Bytes > 0) {
        bufferU8 = (char*)malloc((size_t)utf8Bytes);
    }

    if (utf8Bytes > 0 && !bufferU8) {
        free(bufferW);
        return false;
    }

    if (utf8Bytes > 0) {
        WideCharToMultiByte(CP_UTF8, 0, bufferW, chars, bufferU8, utf8Bytes, NULL, NULL);
    }

    HANDLE file = CreateFileW(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) {
        free(bufferU8);
        free(bufferW);
        return false;
    }

    DWORD written = 0;
    bool ok = true;
    if (utf8Bytes > 0) {
        ok = WriteFile(file, bufferU8, (DWORD)utf8Bytes, &written, NULL) && written == (DWORD)utf8Bytes;
    }
    CloseHandle(file);

    free(bufferU8);
    free(bufferW);

    return ok;
}

bool dotxt_load_into_editor(HWND hwndEdit, const wchar_t* path) {
    if (has_extension(path, L".rtf")) {
        return load_rtf(hwndEdit, path);
    }

    DWORD size = 0;
    BYTE* bytes = read_all_bytes(path, &size);
    if (!bytes) {
        return false;
    }

    wchar_t* text = decode_text_to_utf16(bytes, size);
    free(bytes);

    if (!text) {
        return false;
    }

    SetWindowTextW(hwndEdit, text);
    free(text);
    return true;
}

bool dotxt_save_from_editor(HWND hwndEdit, const wchar_t* path) {
    if (has_extension(path, L".rtf")) {
        return save_rtf(hwndEdit, path);
    }
    return save_utf8_text(hwndEdit, path);
}
