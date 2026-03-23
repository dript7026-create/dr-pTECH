#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <shellapi.h>

#define MAX_PATH_LEN 260
#define MAX_FILES 1000
#define MAX_PROMPT_LEN 512

typedef struct {
    char filename[MAX_PATH_LEN];
    char filepath[MAX_PATH_LEN];
} ConceptFile;

typedef struct {
    ConceptFile files[MAX_FILES];
    int file_count;
    char output_dir[MAX_PATH_LEN];
    char sprite_format[MAX_PROMPT_LEN];
    char bg_format[MAX_PROMPT_LEN];
} ConceptLifeProject;

int scan_directory(const char *path, ConceptFile *files) {
    int count = 0;
    WIN32_FIND_DATAA find_data;
    HANDLE find_handle;
    char search_path[MAX_PATH_LEN];
    
    snprintf(search_path, MAX_PATH_LEN, "%s\\*.png", path);
    find_handle = FindFirstFileA(search_path, &find_data);
    
    if (find_handle == INVALID_HANDLE_VALUE) {
        return 0;
    }
    
    do {
        if (count < MAX_FILES) {
            strcpy_s(files[count].filename, MAX_PATH_LEN, find_data.cFileName);
            snprintf(files[count].filepath, MAX_PATH_LEN, "%s\\%s", path, find_data.cFileName);
            count++;
        }
    } while (FindNextFileA(find_handle, &find_data));
    
    FindClose(find_handle);
    return count;
}

int process_assets(ConceptLifeProject *project) {
    // Minimal implementation: copy found PNGs into output directory.
    if (project->file_count == 0) {
        printf("No files to process.\n");
        return 0;
    }

    // Ensure output directory exists (CreateDirectoryA will fail if it already exists).
    if (!CreateDirectoryA(project->output_dir, NULL)) {
        DWORD err = GetLastError();
        if (err != ERROR_ALREADY_EXISTS) {
            printf("Failed to create output directory '%s' (error %lu)\n", project->output_dir, err);
            return -1;
        }
    }

    int processed = 0;
    for (int i = 0; i < project->file_count; ++i) {
        char dest[MAX_PATH_LEN];
        snprintf(dest, MAX_PATH_LEN, "%s\\%s", project->output_dir, project->files[i].filename);
        if (CopyFileA(project->files[i].filepath, dest, FALSE)) {
            processed++;
            printf("Copied: %s -> %s\n", project->files[i].filepath, dest);
        } else {
            DWORD err = GetLastError();
            printf("Failed to copy %s (error %lu)\n", project->files[i].filepath, err);
        }
    }

    printf("Processed %d/%d files.\n", processed, project->file_count);
    return processed;
}

int open_output_directory(const char *path) {
    ShellExecuteA(NULL, "open", path, NULL, NULL, SW_SHOW);
    return 0;
}

int main(int argc, char *argv[]) {
    ConceptLifeProject project;
    memset(&project, 0, sizeof(project));
    if (argc < 3) {
        printf("Usage: %s <input_dir> <output_dir>\n", argv[0]);
        return 1;
    }

    // Store output directory
    strcpy_s(project.output_dir, MAX_PATH_LEN, argv[2]);

    // Scan input directory for PNGs
    project.file_count = scan_directory(argv[1], project.files);
    printf("Found %d PNG file(s) in '%s'.\n", project.file_count, argv[1]);
    for (int i = 0; i < project.file_count; ++i) {
        printf("  %s\n", project.files[i].filename);
    }

    // Process assets (copy into output dir for now)
    int processed = process_assets(&project);
    if (processed < 0) {
        fprintf(stderr, "Asset processing failed.\n");
        return 1;
    }

    // Open the output directory in Explorer
    open_output_directory(project.output_dir);

    return 0;
}