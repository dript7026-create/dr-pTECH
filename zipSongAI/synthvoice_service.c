#define _CRT_SECURE_NO_WARNINGS
#define UNICODE
#define _UNICODE

#include "synthvoice.h"

#include <stdio.h>
#include <wchar.h>

static void print_usage(void);

static void print_usage(void)
{
    wprintf(L"SynthVoice service commands:\n");
    wprintf(L"  synthvoice_service.exe chat <user> <message>\n");
    wprintf(L"  synthvoice_service.exe schedule-add <title> <due> <tag> [note]\n");
    wprintf(L"  synthvoice_service.exe schedule-list\n");
    wprintf(L"  synthvoice_service.exe diagnostics\n");
    wprintf(L"  synthvoice_service.exe summary\n");
    wprintf(L"  synthvoice_service.exe notify <message>\n");
}

int wmain(int argc, wchar_t **argv)
{
    SynthVoiceBank bank;
    SynthVoicePersonality personality;
    wchar_t buffer[8192];

    synthvoice_bank_load_in_module_dir(&bank);
    synthvoice_personality_load_in_module_dir(&personality);

    if (argc < 2)
    {
        print_usage();
        return 1;
    }

    if (_wcsicmp(argv[1], L"chat") == 0 && argc >= 4)
    {
        wcsncpy(personality.lastUser, argv[2], 63);
        personality.lastUser[63] = 0;
        personality.chatCount += 1;
        synthvoice_personality_chat(&personality, &bank, argv[2], argv[3], buffer, 8192);
        synthvoice_personality_save_in_module_dir(&personality);
        wprintf(L"%ls\n", buffer);
        return 0;
    }

    if (_wcsicmp(argv[1], L"schedule-add") == 0 && argc >= 5)
    {
        if (!synthvoice_personality_add_schedule(&personality, argv[2], argv[3], argv[4], argc >= 6 ? argv[5] : L""))
        {
            fwprintf(stderr, L"Schedule store is full.\n");
            return 2;
        }
        synthvoice_personality_save_in_module_dir(&personality);
        synthvoice_personality_format_schedule_json(&personality, buffer, 8192);
        wprintf(L"%ls\n", buffer);
        return 0;
    }

    if (_wcsicmp(argv[1], L"schedule-list") == 0)
    {
        synthvoice_personality_format_schedule_json(&personality, buffer, 8192);
        wprintf(L"%ls\n", buffer);
        return 0;
    }

    if (_wcsicmp(argv[1], L"diagnostics") == 0)
    {
        synthvoice_personality_format_diagnostics_json(&personality, &bank, buffer, 8192);
        wprintf(L"%ls\n", buffer);
        return 0;
    }

    if (_wcsicmp(argv[1], L"summary") == 0)
    {
        synthvoice_personality_format_summary_json(&personality, &bank, buffer, 8192);
        wprintf(L"%ls\n", buffer);
        return 0;
    }

    if (_wcsicmp(argv[1], L"notify") == 0 && argc >= 3)
    {
        personality.notificationCount += 1;
        synthvoice_personality_format_notification(&personality, argv[2], buffer, 8192);
        synthvoice_personality_save_in_module_dir(&personality);
        wprintf(L"%ls\n", buffer);
        return 0;
    }

    print_usage();
    return 1;
}