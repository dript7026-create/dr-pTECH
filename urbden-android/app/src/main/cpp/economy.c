#include "economy.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static int g_money = 100;
static int g_moral = 0;
static char g_evidence[512];

void economy_init() {
    g_money = 100;
    g_moral = 0;
    g_evidence[0] = '\0';
}

int economy_get_money() { return g_money; }

int economy_apply_delivery(int reward, int moral_effect) {
    g_money += reward;
    g_moral += moral_effect;
    return g_money;
}

int economy_get_moral() { return g_moral; }

void economy_add_evidence(const char* e) {
    if (!e) return;
    strncat(g_evidence, e, sizeof(g_evidence)-strlen(g_evidence)-1);
    strncat(g_evidence, ";", sizeof(g_evidence)-strlen(g_evidence)-1);
}

char* economy_status() {
    char* out = (char*)malloc(256);
    if (!out) return NULL;
    snprintf(out, 256, "Money=%d, Moral=%d, Evidence=%s", g_money, g_moral, g_evidence[0]?g_evidence:"(none)");
    return out;
}
