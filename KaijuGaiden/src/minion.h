#ifndef KAJ_MINION_H
#define KAJ_MINION_H

void minion_manager_init(void);
void minion_spawn(void);
int minion_count(void);
void minion_update_all(void);
int minion_damage_first(int dmg);
void minion_kill_first(void);

#endif // KAJ_MINION_H
