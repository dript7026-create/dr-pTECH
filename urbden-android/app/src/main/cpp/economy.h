#ifndef URBDEN_ECONOMY_H
#define URBDEN_ECONOMY_H

void economy_init();
int economy_get_money();
int economy_apply_delivery(int reward, int moral_effect);
int economy_get_moral();
void economy_add_evidence(const char* e);
char* economy_status(); // caller must free

#endif
