#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// ============================================================================
// SKAZKA: Slavic Folklore Action-RPG - Foundation
// ============================================================================

// Constants
#define WORLD_WIDTH 256
#define WORLD_HEIGHT 256
#define MAX_ENTITIES 512
#define MAX_INVENTORY 32
#define MAX_QUESTS 64

// Enums
typedef enum { WARRIOR, WIZARD, SKOMOROKH } ClassType;
typedef enum { HUMAN, LESHY, DOMOVOI, RUSALKA, ZMEY } NPCType;
typedef enum { SWORD, AXE, BOW, STAFF } WeaponType;
typedef enum { LEATHER, CHAINMAIL, PLATE } ArmorType;
typedef enum { HEALTH, MANA, STAMINA } ResourceType;

// Vector3D for 3D space with 2D rendering
typedef struct {
	float x, y, z;
} Vec3D;

// Item system
typedef struct {
	int id;
	char name[32];
	int type; // 0=weapon, 1=armor, 2=potion, 3=quest
	int value;
	int rarity; // 0=common, 1=rare, 2=epic, 3=legendary
} Item;

// Inventory
typedef struct {
	Item items[MAX_INVENTORY];
	int count;
	int gold;
} Inventory;

// Character stats
typedef struct {
	int level;
	int exp;
	int expToLevel;
	int health;
	int maxHealth;
	int mana;
	int maxMana;
	int stamina;
	int maxStamina;
	int strength;
	int intelligence;
	int endurance;
	int agility;
} Stats;

// Player
typedef struct {
	Vec3D pos;
	ClassType class;
	Stats stats;
	Inventory inventory;
	WeaponType equippedWeapon;
	ArmorType equippedArmor;
	int questsCompleted;
} Player;

// NPC/Enemy
typedef struct {
	int id;
	Vec3D pos;
	NPCType type;
	char name[32];
	int health;
	int maxHealth;
	int level;
	int lootId; // Item drop on defeat
	int isAlly;
} Entity;

// Quest system
typedef struct {
	int id;
	char title[64];
	char description[256];
	int targetEntityId;
	int reward_exp;
	int reward_gold;
	int isComplete;
} Quest;

// World state
typedef struct {
	Player player;
	Entity entities[MAX_ENTITIES];
	int entityCount;
	Quest quests[MAX_QUESTS];
	int questCount;
	int currentTime; // In-game time
	int dayNightCycle;
} GameWorld;

// ============================================================================
// CORE GAME FUNCTIONS
// ============================================================================

void initPlayer(Player *p, ClassType c) {
	p->pos = (Vec3D){128, 128, 0};
	p->class = c;
	p->stats.level = 1;
	p->stats.exp = 0;
	p->stats.expToLevel = 100;
	p->stats.maxHealth = (c == WARRIOR) ? 100 : (c == WIZARD) ? 60 : 80;
	p->stats.health = p->stats.maxHealth;
	p->stats.maxMana = (c == WIZARD) ? 100 : 30;
	p->stats.mana = p->stats.maxMana;
	p->stats.maxStamina = 100;
	p->stats.stamina = p->stats.maxStamina;
	p->stats.strength = (c == WARRIOR) ? 15 : 8;
	p->stats.intelligence = (c == WIZARD) ? 15 : 8;
	p->stats.endurance = 10;
	p->stats.agility = 10;
	p->inventory.count = 0;
	p->inventory.gold = 50;
	p->equippedWeapon = SWORD;
	p->equippedArmor = LEATHER;
	p->questsCompleted = 0;
}

void initGameWorld(GameWorld *world, ClassType playerClass) {
	initPlayer(&world->player, playerClass);
	world->entityCount = 0;
	world->questCount = 0;
	world->currentTime = 0;
	world->dayNightCycle = 1; // 1=day, 0=night
	
	// Populate world with NPCs/enemies based on Slavic folklore
	// Example: Leshy (forest spirit) encounters, Zmey (dragon) boss fights
}

void addEntity(GameWorld *world, Vec3D pos, NPCType type, const char *name, int level, int lootId) {
	if (world->entityCount >= MAX_ENTITIES) return;
	Entity *e = &world->entities[world->entityCount++];
	e->pos = pos;
	e->type = type;
	e->level = level;
	e->health = e->maxHealth = 30 + (level * 15);
	e->lootId = lootId;
	strcpy(e->name, name);
	e->isAlly = 0;
}

void addQuest(GameWorld *world, const char *title, const char *desc, int targetEntity, int expReward, int goldReward) {
	if (world->questCount >= MAX_QUESTS) return;
	Quest *q = &world->quests[world->questCount++];
	q->id = world->questCount;
	strcpy(q->title, title);
	strcpy(q->description, desc);
	q->targetEntityId = targetEntity;
	q->reward_exp = expReward;
	q->reward_gold = goldReward;
	q->isComplete = 0;
}

void combatSystem(Player *p, Entity *e) {
	int playerDamage = p->stats.strength + (rand() % 10);
	int enemyDamage = e->level * 3 + (rand() % 8);
	
	// Simple turn-based combat
	printf("[COMBAT] %s vs %s\n", "Player", e->name);
	
	while (p->stats.health > 0 && e->health > 0) {
		e->health -= playerDamage;
		printf("Player deals %d damage. Enemy health: %d\n", playerDamage, e->health);
		
		if (e->health <= 0) {
			printf("[VICTORY] %s defeated!\n", e->name);
			p->stats.exp += e->level * 25;
			p->inventory.gold += e->level * 10;
			return;
		}
		
		p->stats.health -= enemyDamage;
		printf("Enemy deals %d damage. Player health: %d\n", enemyDamage, p->stats.health);
	}
	
	if (p->stats.health <= 0) {
		printf("[DEFEATED] You have fallen...\n");
		p->stats.health = p->stats.maxHealth / 2;
		p->pos = (Vec3D){128, 128, 0}; // Respawn
	}
}

void levelUp(Player *p) {
	if (p->stats.exp >= p->stats.expToLevel) {
		p->stats.level++;
		p->stats.exp = 0;
		p->stats.expToLevel = (int)(p->stats.expToLevel * 1.2);
		p->stats.maxHealth += 15;
		p->stats.health = p->stats.maxHealth;
		p->stats.strength += 2;
		p->stats.intelligence += 2;
		printf("[LEVEL UP] You are now level %d!\n", p->stats.level);
	}
}

void gameLoop(GameWorld *world) {
	printf("=== SKAZKA: Slavic Folklore RPG ===\n");
	printf("Player at: (%.1f, %.1f, %.1f)\n", world->player.pos.x, world->player.pos.y, world->player.pos.z);
	printf("Health: %d/%d | Mana: %d/%d | Gold: %d\n", 
		   world->player.stats.health, world->player.stats.maxHealth,
		   world->player.stats.mana, world->player.stats.maxMana,
		   world->player.inventory.gold);
	printf("Level: %d | EXP: %d/%d\n", world->player.stats.level, world->player.stats.exp, world->player.stats.expToLevel);
}

int main() {
	srand((unsigned)time(NULL));
	
	GameWorld world = {0};
	initGameWorld(&world, WARRIOR);
	
	// Example: Add some Slavic folklore entities
	addEntity(&world, (Vec3D){150, 150, 0}, LESHY, "Leshy Guardian", 5, 1);
	addEntity(&world, (Vec3D){200, 200, 0}, ZMEY, "Zmey Gorynych", 15, 2);
	
	// Example: Add quests
	addQuest(&world, "Defeat the Leshy", "The forest spirit threatens the village", 0, 250, 100);
	addQuest(&world, "Slay Zmey Gorynych", "The three-headed dragon must be stopped", 1, 1000, 500);
	
	// Main game loop
	for (int i = 0; i < 3; i++) {
		gameLoop(&world);
		levelUp(&world.player);
	}
	
	printf("\n[Game Foundation Ready]\nExpand with:\n- Advanced AI\n- Dialogue system\n- Inventory management\n- Map generation\n- Rendering layer\n");
	
	return 0;
}