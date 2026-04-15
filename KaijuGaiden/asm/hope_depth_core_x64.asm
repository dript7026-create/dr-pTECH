default rel

section .text align=16

global hope_depth_strength_i32
global hope_depth_project_x_i32
global hope_depth_project_y_i32

; int hope_depth_strength_i32(int brightness, int proximity, int eye_open, int motion, int preset_bias)
; Returns a clamped 0..255 inward-depth strength for the Windows HOPE lane.
hope_depth_strength_i32:
    mov eax, ecx
    imul eax, 2
    add eax, edx
    add eax, r8d
    mov r10d, r9d
    imul r10d, 3
    add eax, r10d
    mov r10d, dword [rsp + 40]
    imul r10d, 4
    add eax, r10d
    cmp eax, 0
    jge .non_negative
    xor eax, eax
    ret

.non_negative:
    cmp eax, 255
    jle .done
    mov eax, 255

.done:
    ret

; int hope_depth_project_x_i32(int x, int scene_center, int band_depth, int strength, int focus_px)
; Reprojects a point inward toward scene_center. Higher strength and focus increase inward pull.
hope_depth_project_x_i32:
    mov eax, ecx
    sub eax, edx
    mov r10d, dword [rsp + 40]
    add r10d, 64
    imul r8d, r9d
    imul r8d, r10d
    mov ecx, 16384
    cdq
    idiv ecx
    sub eax, dword [rsp + 40]
    add eax, edx
    ret

; int hope_depth_project_y_i32(int y, int scene_center, int band_depth, int strength, int focus_px)
; Reprojects a y coordinate inward toward the vertical focus plane with a gentler response.
hope_depth_project_y_i32:
    mov eax, ecx
    sub eax, edx
    mov r10d, dword [rsp + 40]
    sar r10d, 1
    add r10d, 48
    imul r8d, r9d
    imul r8d, r10d
    mov ecx, 24576
    cdq
    idiv ecx
    sub eax, dword [rsp + 40]
    add eax, edx
    ret