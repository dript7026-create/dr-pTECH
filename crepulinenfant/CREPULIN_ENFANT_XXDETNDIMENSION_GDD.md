# Crepulin: Enfant; .xxDetnDimension

## Document Basis
This GDD is a grounded consolidation built from the currently available sources:
- `Crepulin_Enfant_DetnDimension.c`, which exists as an empty target source file.
- `detn_idletoward_sprite.clip` and `detn_walktoward_sprite.clip`, which indicate an early forward-facing character animation direction.
- public web-visible creator-handle traces tied to `Ryan Richard Carell`, `rrcarell`, `GXREMEVK`, and `rxndvll`, which suggest a rough industrial, underground, beat-driven aesthetic profile.
- Russian and Soviet folklore and urban-legend motifs including household spirits, nightmare entities, haunted furnishings, black car abduction rumors, infernal drilling myths, and disaster omens.

This document is therefore not a recovery of an older lost GDD. It is the first full design consolidation for the project.

## High Concept
Crepulin: Enfant; .xxDetnDimension is a 2.5D horror action-adventure about a child navigating a parasitic mirror-layer hidden inside an aging apartment district. The player character, Enfant, slips into the DetnDimension, a folded city-space made from household superstition, abandoned civic infrastructure, and predatory memory residue called Crepulin. To survive, Enfant must bargain with house spirits, outmaneuver nightmare predators, and trace a chain of disappearances tied to a black vehicle that travels through walls, stairwells, and underground service roads as if the city itself were a closed circuit.

## Core Pillars
1. Child-scale horror through familiar spaces made wrong.
2. Folklore-infused systems: domestic spirits, nightmare rules, taboo objects, and ritual exchanges.
3. Tension between stealth, pursuit, and intimate close-quarters survival.
4. Environmental storytelling through corridors, courtyards, bathhouses, rail lines, and communal interiors.
5. Strong visual identity built from frontal sprite presentation, decayed civic textures, and occult-industrial sound.

## Product Definition
- Genre: 2.5D horror action-adventure with light metroidvania structure.
- Camera: primarily side-on exploration with frontal confrontation frames for dialogue, threat reveals, and ritual moments.
- Target platform assumption: desktop prototype first, low-level C implementation path retained.
- Target playtime: 8 to 12 hours for main path, 14 hours with all myth routes resolved.
- Rating target: Teen to Mature depending on final horror intensity.

## Why the Project Looks This Way
The two existing Clip Studio Paint files are named as forward-facing idle and walk sprite studies for `detn`, which strongly suggests the project's earliest visual instinct is not a distant side-profile platform hero but a character who confronts the player head-on. That should remain central. Enfant should often face toward camera during dread states, negotiation scenes, and approach sequences.

The public creator-handle traces found online suggest an adjacent creative identity shaped by underground beat culture, abstract track naming, occult phrasing, lo-fi intensity, and rough industrial mood. That should inform the sound palette, naming conventions, and editing rhythm without turning the project into a music visualizer.

## World Premise
Crepulin is the name residents give to the dusk-film that gathers in neglected living spaces where fear, silence, and old rituals overlap. Most people think it is mold, soot, or trauma. In truth, it is a memory-reactive residue that binds urban legends into spatial reality. When enough Crepulin accumulates, the DetnDimension appears: a child-scaled mirror-city built from corridors, kitchens, elevators, pipes, yards, stations, and burial cavities that have absorbed generations of warnings told to keep children alive.

The DetnDimension is not hell, dreamland, or cyberspace. It is an echo architecture of inherited caution. Every legend becomes a route rule, every taboo object a gate, every household spirit a possible ally or judge.

## Main Characters

### Enfant
The playable child protagonist. Enfant is not defined by a single conventional biography at first. The ambiguity is intentional. Different adults project different names and expectations onto the child, but the DetnDimension reacts only to the title `Enfant`, treating the protagonist as a representative child-presence rather than a single biography. Enfant is observant, quiet, brave in bursts, and capable of learning ritual rules faster than adults can. Movement should feel small, vulnerable, and precise.

### Crepulin
Crepulin is both a substance and a semi-sentient distributed antagonist. It accumulates where neglect and fear repeat. It alters geometry, attracts predators, stores echoes, and lets legends become spatially enforceable. It does not speak in full sentences. It communicates through stain patterns, breathing walls, child-height scrawls, and repeated audio fragments.

### The Domov Keeper
An ambiguous house-spirit derived from the Domovoy tradition. In safe states it protects Enfant, unlocks hidden domestic passages, warns of bad thresholds, and rearranges dropped tools into useful clusters. In anger it becomes territorial and punishing. The player must keep rooms orderly enough, or at least ritually respectful enough, to maintain its aid.

### The Keyhole Kikimora
A recurring stalker entity born from the nightmare tradition of the Kikimora. It enters through cracks, keyholes, vents, curtain folds, and half-open wardrobes. It is tied to sleeping rooms, abandoned children's furniture, and domestic disorder. The Kikimora is not a single boss at first. It is an ambient systemic hunter that later manifests as a named adversary.

### Babka Kuroles
An original threshold-guide figure inspired by Baba Yaga, but localized to courtyards, bathhouse steam, and maintenance lots rather than a forest. She lives inside a mobile service hut mounted on collapsed utility stilts and acts as the world's most dangerous mentor. She offers true advice at a price and false advice if disrespected.

### The Chauffeur of the Black Road
The game's principal recurring pursuer. Inspired by the Black Volga legend, this entity travels in a black government-style vehicle with pale curtains, no readable driver face, and horn-like mirrors. It is associated with child disappearance, false authority, and timing-based death prophecies. The Chauffeur speaks politely, which makes it worse.

### The Bird Over Reactor Nine
An omen creature modeled after late Soviet disaster-bird folklore. It appears before major collapse events in the DetnDimension. It may be warning Enfant, or merely feeding on approaching catastrophe.

## Narrative Summary
Enfant lives in a decaying apartment district informally called Block Nine, a place of sealed service corridors, communal kitchens, abandoned courtyards, old bathhouses, and half-finished rail extensions. Children whisper about the Black Car, the curtain room, the keyhole woman, and the hole that speaks. Adults dismiss these stories but still follow their rules in small ways.

One night, after a blackout and a prolonged elevator failure, a child from the block disappears. Enfant follows signs into maintenance spaces and slips into the DetnDimension. There, folklore is no longer symbolic. Rooms listen. Curtains hunt. The wrong baths remember births and deaths. Household spirits demand ritual courtesy. The Black Road loops under every district. To bring the missing child or children back, Enfant must understand the laws that adults forgot they were obeying.

## Full Narrative Structure

### Prologue: The Courtyard Warning
The game opens in Block Nine's courtyard during evening. Children trade rumors about a black car that asks the time. A grandmother warns Enfant never to answer strangers in service lanes, never sleep facing a mirror, and never leave curtains half-tied. The tutorial establishes movement, hiding, listening, and object interaction. A blackout cuts the scene. An elevator opens on the wrong floor. Someone goes missing.

### Act I: Stairwell Mouth
Enfant descends through stairwells, fuse closets, pipe shafts, and utility rooms. The first crossing into the DetnDimension occurs when a service corridor stretches impossibly long. The Domov Keeper tests Enfant through a simple domestic rite: restore order to a vandalized room, return bread and salt to the stove niche, and the hidden passage opens. The act establishes the `House Rule` system and culminates in the first Black Road sighting.

### Act II: Curtain Flats
The player explores apartment interiors warped by the yellow and black curtain legends. Curtains can become traps, masks, or portals depending on light and ritual preparation. The Keyhole Kikimora begins active pursuit here. Enfant learns that children who vanished were often last seen in rooms adults had recently renovated or sealed. The act ends with a mini-boss encounter in a nursery where curtains must be cut in the correct order to break a looping death script.

### Act III: Bathhouse Veins
This zone expands into communal bathhouses, steam chambers, laundry ducts, and heated crawlspaces. Babka Kuroles appears in her stilted service hut and introduces barter-based myth logic. She explains that the DetnDimension keeps children because adults keep outsourcing warning, memory, and care to superstition instead of responsibility. Enfant gains the ability to carry `Warmth`, a temporary protective state tied to steam and candles.

### Act IV: Railbone Yards
Old tracks, signal sheds, and underground platforms reveal that the Black Road is not merely a car route but a transit principle. Vehicles, hearses, ambulances, and service vans can all become masks for the same predator. Enfant finds records suggesting disappearances span decades. The Bird Over Reactor Nine starts appearing before collapses and chase scenes. The act ends with a timed pursuit through dead rail tunnels while the Chauffeur predicts Enfant's route aloud.

### Act V: Well Chamber
The DetnDimension deepens into bore shafts, drilling rooms, echo wells, and a chamber where recorded voices repeat from impossible depth. This act incorporates the infernal drilling myth. Enfant discovers that the city once buried both industrial accidents and unofficial child deaths inside unmarked utility expansions. The hole is not literally hell, but it is a truth pit where denied catastrophe accumulates. The player must descend without listening too long to the voices.

### Act VI: The Black Road Procession
The Black Road opens fully under the district. The Chauffeur collects not only children but also names, deadlines, and unlived futures. The final run alternates stealth, escape, and ritual counterplay. Enfant uses everything learned from the Domov Keeper, Babka Kuroles, and domestic taboo systems to reverse the road's authority. The last confrontation occurs in a parking vault where apartment windows, rail lights, bath steam, and funeral curtains all feed the same moving threshold.

### Ending
Enfant escapes with some of the missing children, but the ending should resist total closure. The district remains marked. Adults finally speak openly about what they ignored. Some rooms become safe because they are named truthfully again. Others remain sealed. A final stinger reveals that Crepulin never fully disappears. It recedes when care returns.

## Setting Breakdown

### Block Nine Surface Layer
- courtyards
- apartment entry halls
- broken elevators
- utility sheds
- bus stops

### DetnDimension Layer
- stretched stairwells
- corridor loops
- curtain rooms
- stove niches and hidden wall cavities
- bathhouse steam ribs
- railbone yards
- the black road vaults
- the well chamber

## Core Mechanics

### Exploration
Enfant traverses 2.5D spaces with ladders, ledges, crawl openings, window sills, vent passages, and child-sized shortcuts. World readability must come from repeated domestic shapes becoming distorted rather than from generic fantasy platforming.

### Hiding
Hide spots include beds, tables, laundry carts, alcoves, and behind hanging curtains. Not all hide spots are safe against all threats. Some spirits ignore conventional hiding and instead respond to ritual correctness.

### Listening
The player can stop and `listen` to walls, vents, doors, and floors. Listening reveals enemy routes, false walls, spirit mood, and whether a room is under a harmful legend-state. Over-listening near the Well Chamber or Crepulin-heavy zones builds Dread.

### House Rule System
Rooms and buildings each have embedded rules. Examples:
- Do not leave bread on the floor.
- Do not face the mirror while sleeping.
- Do not answer a voice from the corridor after midnight unless you know the name.
- Do not cross a steam room threshold cold.

When Enfant respects a rule, spirits may aid the player. When rules are broken, rooms become hostile.

### Dread and Warmth
- Dread rises during pursuit, in corrupted rooms, or while hearing forbidden sounds.
- Warmth is gained through candles, stoves, bath steam, shared rooms, and certain spirit blessings.
- High Dread distorts controls, audio, and vision.
- Warmth suppresses Dread and protects against specific predators.

### Tools
Enfant does not carry military gear. Tools are domestic, improvised, and symbolic:
- candle stub
- box cutter
- key ring
- iron spoon
- thread spool
- chalk
- bread and salt packet
- hand bell
- glass marble

Each tool has both practical and folkloric use.

### Pursuit Encounters
The Black Road sequences, Kikimora lunges, and room collapse events are short, high-intensity escape encounters. These should be readable and fair. Horror comes from anticipation and rule pressure, not random unavoidable failure.

### Spirit Bargains
The Domov Keeper and Babka Kuroles trade in tasks rather than currency. They ask for:
- restored order
- returned keepsakes
- correct offerings
- truthful answers
- memory fragments

### Progression
Progression is ability-gated by understanding and ritual competence rather than stats. Key unlocks include:
- House Listening
- Warmth Carry
- Curtain Cut Rite
- Stove Blessing
- Bath Steam Passage
- Black Road Refusal
- Name Ward

## Enemy and Threat Design

### Keyhole Kikimora
Primary domestic nightmare stalker. Enters through tiny openings. Weak to orderly rooms, light placed at child height, and certain noise lures.

### Curtain Hands
Manifest only in rooms under cursed textile states. They are less enemies than trap-events with tell patterns.

### Boiler Men
Overheated municipal workers half-fused to infrastructure. Patrol bathhouse and pipe zones.

### Chalk Children
Echo silhouettes left by previous missing kids. Some guide. Some mislead.

### The Chauffeur
Primary recurring pursuer. Embodies false authority, timed doom, and civic secrecy.

### Crepulin Blooms
Stationary environmental hazards that spread if untreated. They alter geometry and audio.

## Level Design Principles
1. Every zone must begin from a familiar urban shape.
2. Distortion must escalate logically from neglect, memory, or taboo violation.
3. Child-scale routes should reward observation rather than brute force.
4. Repeated landmarks should gain new meaning under different legend states.
5. Horror reveals should be staged through absence, sound, and implication before direct confrontation.

## Visual Direction
The protagonist should read clearly as a forward-facing child sprite with strong silhouette on low light backgrounds. The world should look damp, plaster-flaked, sodium-lit, mold-stained, and ritual-marked. Avoid overclean fantasy polish. Surface materials should feel touched, repaired, layered, and inhabited.

Primary palette:
- nicotine yellow
- dead teal
- stairwell green
- sodium orange
- bathhouse white steam
- bruised violet shadow
- black lacquer vehicle shine
- chalk white and rust red accents

## Audio Direction
The sound world should merge apartment ambience, industrial drone, lo-fi beat textures, tape wow, low choir, distant train resonance, and nervous child-scale foley. This is where the public handle traces matter: the game should feel rhythmically edited by someone adjacent to underground beatmaking, not like generic orchestral horror.

Key audio references in mood terms:
- warped cassette hiss
- hollow kick drum as distant utility thump
- broken vocal sample loops
- radiator percussion
- black-car engine purr as bass texture
- whispered children counting in stereo drift

## Interface Direction
UI should resemble utility labels, maintenance notes, prayer cards, elevator diagrams, and child chalk marks. Menus should feel hand-annotated, not corporate.

## Systemic Folklore Integration

### Domovoy Integration
Household spirits protect kin and punish disorder. In game terms, this becomes a room-state system and ally logic.

### Kikimora Integration
Nightmare keyhole and house spirit behavior becomes both stealth enemy design and sleep-room hazard logic.

### Baba Yaga Integration
The threshold witch becomes Babka Kuroles, a moving-service-hut mentor who governs liminal movement and dangerous bargains.

### Black Volga Integration
The black-child-abductor vehicle becomes the Black Road system and the Chauffeur antagonist.

### Yellow and Black Curtains Integration
Domestic textile myths become the logic basis for Curtain Flats and fabric trap states.

### Well to Hell Integration
The infernal borehole myth becomes a truth-pit where denied civic catastrophe accumulates and speaks back.

### Black Bird of Chernobyl Integration
The omen bird becomes a disaster herald for collapse sequences and late-game prophecy.

## Asset Direction Inferred from Existing Clip Files
- The `detn_idletoward_sprite.clip` file suggests a frontal idle presentation for Enfant.
- The `detn_walktoward_sprite.clip` file suggests a forward walk or approach cycle rather than purely lateral locomotion.
- Both files use the Clip Studio Paint container signature associated with chunked binary project data, which implies they are substantial authored art references rather than placeholders.

These should guide the first playable prototype art set:
- forward-facing idle
- forward approach walk
- front-lit fear pose
- front-facing ritual hold pose
- side walk and crouch support sets

## Prototype Scope Recommendation
Build a vertical slice covering:
1. courtyard tutorial
2. stairwell transition
3. one curtain-room puzzle
4. one Domov Keeper bargain
5. one short Black Road chase

## Implementation Roadmap
1. Define core movement, hiding, listening, and Dread/Warmth systems in C.
2. Create a minimal room-state system for House Rules.
3. Hook the first Enfant idle/walk sprite references into a prototype renderer.
4. Build one district slice: Stairwell Mouth plus Curtain Flats intro.
5. Add the Domov Keeper and Kikimora as the first two systemic threats.
6. Add the Black Road chase sequence as the first cinematic pursuit.

## Handoff Summary
Crepulin is currently a minimal scaffold project with no prior authored GDD in the workspace. This document establishes the first complete design direction and binds it to the only verified local references: the empty source target, the two Detn sprite `.clip` files, the creator-handle mood traces, and the collected Russian/Soviet folklore motifs.