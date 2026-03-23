/*
 * OrbSeeker - idtech2 (Quake II) game module stub
 *
 * This file is a starting point for porting OrbSeeker to an idtech2 based engine.
 * It contains example entity hooks for an `orb` pickup, the island hub spawn
 * and basic comments showing where to integrate the full gameplay loop.
 *
 * To complete the port, integrate with the Quake II SDK `g_local.h` and the
 * game DLL build process. The functions here are intentionally minimal and
 * illustrative; they must be adapted to your chosen SDK's APIs and compiled
 * into the engine's `game` module.
 */


#include "g_local.h"

/*
 * More complete Quake II SDK-compatible example for an `orb` pickup and simple
 * island initialization. This file is still a starting point and requires the
 * Quake II SDK headers and build environment.
 */

/* Orb touch: give player an orb counter and trigger guardian spawn */
void orb_touch(edict_t *self, edict_t *other, cplane_t *plane, csurface_t *surf)
{
    if (!other->client)
        return;

    // Using player persistent data: create a custom field in client->resp or pers.
    // Many mods add custom fields to player state; here we'll use resp.objectives as a placeholder.
    if (!other->client)
        return;

    // Safely increment an orb counter (example uses an invented field `orb_count` attached to resp)
    if (!other->client->ps.stats[STAT_CLIENTS_READY])
        other->client->ps.stats[STAT_CLIENTS_READY] = 0; // placeholder init

    other->client->ps.stats[STAT_CLIENTS_READY] += 1; // increment orb count (replace with real field)

    // Feedback
    gi.cprintf(other, PRINT_HIGH, "You have acquired an Orb!\n");
    gi.sound(other, CHAN_ITEM, gi.soundindex("items/orb_pickup.wav"), 1, ATTN_NORM, 0);

    // Spawn guardian at orb position; implement guardian separately
    spawn_orb_guardian(self->s.origin);

    G_FreeEdict(self);
}

/* Spawn the orb item into the world */
void SP_item_orb(edict_t *self)
{
    if (!self)
        return;

    self->s.modelindex = gi.modelindex("models/items/orb/tris.md2");
    self->solid = SOLID_TRIGGER;
    self->movetype = MOVETYPE_TOSS;
    self->classname = "item_orb";
    self->touch = orb_touch;
    gi.setmodel(self, self->s.modelindex ? "models/items/orb/tris.md2" : "models/items/orb/tris.md2");
    gi.linkentity(self);
}

/* Island hub initialization called from mapspawn or worldspawn handler */
void InitOrbSeekerIsland(void)
{
    // Spawn the raft entity at a fixed shore position
    edict_t *raft = G_Spawn();
    VectorSet(raft->s.origin, 256, 0, 64);
    raft->classname = "raft";
    raft->solid = SOLID_BBOX;
    gi.setmodel(raft, "models/props/raft/tris.md2");
    gi.linkentity(raft);

    // Spawn the monkey companion as a non-solid scripted NPC
    edict_t *monkey = G_Spawn();
    VectorSet(monkey->s.origin, 240, -16, 80);
    monkey->classname = "monkey_companion";
    monkey->movetype = MOVETYPE_STEP;
    gi.setmodel(monkey, "models/monsters/monkey/tris.md2");
    gi.linkentity(monkey);

    // Optionally spawn a few farm-plot triggers (simple entity placeholders)
    for (int i=0; i<3; i++) {
        edict_t *plot = G_Spawn();
        VectorSet(plot->s.origin, 200 + i*32, 40, 40);
        plot->classname = "farm_plot";
        gi.setmodel(plot, "models/props/plot/tris.md2");
        gi.linkentity(plot);
    }

    gi.dprintf("OrbSeeker Island initialized.\n");
}

/* Guardian boss - simple placeholder with health and think function */
void orb_guardian_think(edict_t *self)
{
    // Simple wander/attack placeholder; real implementation should perform
    // rhythm-based QTE interactions and phase logic.
    if (self->health <= 0) {
        // drop orb
        edict_t *orb = G_Spawn();
        VectorCopy(self->s.origin, orb->s.origin);
        SP_item_orb(orb);
        G_FreeEdict(self);
        return;
    }

    // schedule next think
    self->nextthink = level.time + 0.1;
}

void spawn_orb_guardian(vec3_t origin)
{
    edict_t *ent = G_Spawn();
    VectorCopy(origin, ent->s.origin);
    ent->classname = "orb_guardian";
    ent->s.modelindex = gi.modelindex("models/monsters/guardian/tris.md2");
    ent->health = 400;
    ent->think = orb_guardian_think;
    ent->nextthink = level.time + 0.1;
    gi.linkentity(ent);
}

/* Example of registration - call from game initialization (SDK-specific)
 * In many SDKs you register spawn functions via a function table. Add an
 * entry that maps the entity classname in the .map to SP_item_orb, etc.
 */

