# Kaiju Gaiden Boss Design Profiles

This document turns the current boss roster into explicit asset-direction briefs.
It is intended to make every boss read as a distinct creature family with grounded anatomy, believable materials, and clear animation priorities before final sprite-sheet production.

These profiles are derived from the current campaign tables in KaijuGaiden/kaijugaiden.c, especially:

- stage name and boss name tables
- horror-genre framing
- stage ecology and hazard lines
- boss prefab and subarchetype routing
- current Logora and Goolloki identity work

Each profile is written to answer one production question: what should the default boss art communicate at a glance, even in low-resolution sprite form?

## Shared Rules

- Every boss should read as one dominant animal logic plus one environmental mutation, not as an arbitrary monster collage.
- Anatomical exaggeration is allowed, but joint placement, weight, and locomotion should still feel physically convincing.
- Heads, shoulders, and forward-most attack limbs should remain readable in silhouette before texture detail is added.
- Phase escalation should intensify posture, injury, exposure, bloom, cracking, or ritual activation instead of replacing the creature with a different design.
- Minions should look ecologically related to the boss, either as brood, scavengers, cult attendants, parasites, or biome-mutated pack life.

## HARBOR LEVIATHAN

- Stage: Harbor Shore
- Horror frame: Abyssal Gothic
- Runtime anchor: Prefab 0, subarchetype 0
- Core animal read: Harbor crocodilian crossed with a reef eel and a whale-jawed scavenger.
- Real anatomy anchors: Broad river-croc skull, lateral eel flexibility through the torso, whale-like throat pleats under the neck, seal-like shoulder fat around the forebody.
- Surface and materials: Barnacled hide, torn dock-rope scars, wet algae film on the spine, shellfish growth around jaw seams and elbows.
- Silhouette priority: Long low skull, heavy front half, tapering tail mass, dorsal reef spines breaking the back line.
- Signature face details: One eye clouded by salt damage, lower jaw slightly asymmetrical, baleen-like fringe mixed with broken teeth at the rear mouth.
- Motion profile: Slow anchor-weight idle, sudden lateral sweep, head-led lunges, tidal drag in phase three.
- Contamination signature: Salt-bloom toxicant wash, oil-film respiratory burden, and undertow plasmic drag that makes the body read chemically heavy rather than merely wet.
- Phase escalation: Phase one is tidal patience, phase two exposes broken rib plating and aggressive shoulder lift, phase three opens the maw wider and sheds surf and foam around the spine.
- Minion ecology: Reef spitters and drowned scavengers should feel like creatures that feed in its wake.
- Asset priority notes: Push wet weight and jaw credibility first; avoid turning it into a generic dragon.

## CINDER WYRM

- Stage: Ash Barrows
- Horror frame: Folk Pyre Curse
- Runtime anchor: Prefab 1, subarchetype 1
- Core animal read: Burnt serpent-drake built from funeral-pyre anatomy rather than volcanic fantasy dragon anatomy.
- Real anatomy anchors: Constrictor neck movement, monitor-lizard foreclaws, emaciated horse-rib barrel, soot-thin bat membrane remnants at the shoulder blades.
- Surface and materials: Carbon-black scale plates split by ember seams, chalk ash caked in skin folds, heat-cracked horn ridges, smoke leaking from old wound vents.
- Silhouette priority: Long neck arc, hollow chest, shovel-claw forelimbs, ember tail taper.
- Signature face details: Charred beak-like snout, recessed ember eyes, split horn crown like half-burned wicker antlers.
- Motion profile: Coiling feints, ash coughs, low creeping circles, sudden reared strike with neck whip.
- Contamination signature: Soot toxicants, ember-breath irritants, and heat-dried fluid collapse that turns every exhale into a corrosive funeral plume.
- Phase escalation: Phase one is smoldering restraint, phase two vents more internal heat through rib cracks, phase three glows through the sternum and throat with more skeletal exposure.
- Minion ecology: Brute cinder pack units should feel like pyre-fed carrion reptiles and coal-hound attendants.
- Asset priority notes: Favor cremation imagery and heat fractures over lava fantasy cliches.

## ROOT BASTION

- Stage: Mangrove Teeth
- Horror frame: Swamp Body Dread
- Runtime anchor: Prefab 2, subarchetype 2
- Core animal read: Mangrove rhinoceros-tortoise fused with strangler-root architecture.
- Real anatomy anchors: Tortoise chest depth, boar shoulder drive, rhino head wedge, mangrove buttress roots functioning as extra limb braces.
- Surface and materials: Water-dark bark hide, fungal bloom under armor seams, root-whisker tangles around knees, mud trapped inside plated bark scales.
- Silhouette priority: Forward shielded head, stacked root shoulders, broad dome shell line, dragging root-beard underneath.
- Signature face details: Buried eyes under bark brows, tusk-like root protrusions, nostril vents hidden in moss folds.
- Motion profile: Low crushing advance, rooted brace before impact, trunk-twist when turning, short explosive gore instead of sprinting.
- Contamination signature: Fungal spores, tannic swamp irritants, and root-sap stasis pressure that make the creature feel overgrown and chemically congested.
- Phase escalation: Phase one is fortress stillness, phase two cracks the bark and reveals living muscle-root bundles, phase three blossoms fungal sores and aggressive lash-vines.
- Minion ecology: Harasser root den creatures should resemble half-grown offshoots or parasitic grove defenders.
- Asset priority notes: Keep it feeling grown, not manufactured; the armor should read as living tree structure.

## GLACIER MAW

- Stage: Frost Breaker
- Horror frame: Arctic Cannibal
- Runtime anchor: Prefab 3, subarchetype 0
- Core animal read: Polar-bear and seal predator stretched into a glacial tunnel hunter.
- Real anatomy anchors: Bear forequarters, walrus neck thickness without tusks, snow-leopard hind mobility, lamprey-style secondary throat folds.
- Surface and materials: Frost-burnt fur patches over pale hide, translucent ice rime along the spine, cracked lip tissue, blood diluted into pink snow around joints.
- Silhouette priority: Massive forelimbs, lowered head, tunnel-like maw opening, back line that feels wind-carved rather than plated.
- Signature face details: Black dead nose against white tissue, deep mouth tunnel ringed with recurved feeding teeth, tiny heat-seeking eyes.
- Motion profile: Short stalking steps, sudden pounce compression, heavy forepaw slams, cold-breath recoil.
- Contamination signature: Frost-bite insolvent impurities, blood-thin respiratory strain, and brittle plasmic instability that make breath clouds feel medically dangerous.
- Phase escalation: Phase one is starving patience, phase two adds shredded lip exposure and harder slam posture, phase three opens the throat wider and throws more snow, frost, and body tremor.
- Minion ecology: Wolfpack rush units should feel like smaller snow-starved relatives or competing scavengers.
- Asset priority notes: This should feel like a believable famine predator first, ice monster second.

## VAULT SERPENT

- Stage: Sunken Vault
- Horror frame: Crypt Gothic
- Runtime anchor: Prefab 4, subarchetype 1
- Core animal read: Ossuary constrictor with cathedral eel traits and relic-guardian posture.
- Real anatomy anchors: Python body logic, moray head reach, humanoid rib-cage echoes built into the hood and neck structure, monk-like folded posture when idle.
- Surface and materials: Polished crypt stone over scaled tissue, gold tarnish in cracks, saint-bone ornament growth, wet mildew on lower coils.
- Silhouette priority: Raised reliquary hood, long ceremonial neck, heavy rear coil base, ribbed crest framing the head.
- Signature face details: Skull-mask brow line, narrow lantern eyes, split jaw hinges that open farther than expected.
- Motion profile: Measured shrine-guardian sway, sudden coil lash, gate-holding lane control, close-range body crush.
- Contamination signature: Tomb mildew corrosives, reliquary dust irritants, and stagnant coil stasis that suggest centuries of sealed toxic atmosphere.
- Phase escalation: Phase one is sealed ritual poise, phase two unlocks faster coil crossings, phase three breaks ornament plates and reveals raw wet serpent muscle under liturgical shell.
- Minion ecology: Crypt choir guards should feel like smaller blind retainers, bone singers, or drowned acolytes.
- Asset priority notes: Avoid generic naga tropes; it should feel like a buried sacred animal forced back into violence.

## SHARD COLOSSUS

- Stage: Glass Delta
- Horror frame: Glass Slasher
- Runtime anchor: Prefab 5, subarchetype 2
- Core animal read: Floodplain ungulate giant cut from mirrored mineral growth and butchered musculature.
- Real anatomy anchors: Moose chest mass, cassowary leg tension, antelope tendon definition, crocodile tail counterweight adapted into blade-like glass growth.
- Surface and materials: Semi-opaque silica plates, mirrored fracture faces, raw tendon visible between shard armor, silt and blood trapped under transparent edges.
- Silhouette priority: High blade shoulders, knife antlers or crest fins, narrow waist, dangerous lower-leg reach.
- Signature face details: Split reflective mask, too many eye glints from fractured sockets, mouth corners torn by internal crystal pressure.
- Motion profile: Stutter-step skating, cutting pivots, diagonal lane control, brittle-looking but very fast recoveries.
- Contamination signature: Silica shard aerosols, mirrored blood-neural scatter, and fracture-born plasmic shimmer that make the air around it feel lacerating.
- Phase escalation: Phase one is elegant and sharp, phase two shows more broken edges and unstable asymmetry, phase three sheds fragments constantly and moves with reckless slasher momentum.
- Minion ecology: Shard mimic pairs should look like broken offspring or detached reflective organ growths.
- Asset priority notes: Keep the glass believable as mineral growth over flesh, not as magic energy armor.

## LOGORA RAPTORMOTH

- Stage: Thunder Reef
- Horror frame: Tokusatsu Sky Dread
- Runtime anchor: Prefab 6, subarchetype 0
- Core animal read: Reef-nesting raptor fused with storm moth display anatomy.
- Real anatomy anchors: Hawk sternum and shoulder mechanics, cassowary hind-leg aggression, moth thorax fluff around the chest, manta-like wing membrane breaks toward the trailing edge.
- Surface and materials: Rain-slick feather scales, powdery moth bloom near the neck, lightning-burn vein lines across crest plates, salt-white claws.
- Silhouette priority: Tall strike crest, sickle forelimbs, broad triangular wing flare, compact predatory torso.
- Signature face details: Hooked beak-jaw hybrid, forward hunting eyes, cheek fans that open like moth false-eyes during threat display.
- Motion profile: High alert bounce, wing-assisted sidestep, sudden downward rake, storm-display full flare during windup.
- Contamination signature: Ozone-tainted reef mist, storm-pollen respiratory agitation, and charged plasmic flicker that turns each wingbeat into an atmospheric hazard.
- Phase escalation: Phase one hunts and tests lanes, phase two widens the crest and exposes brighter storm patterning, phase three becomes more ragged and electric with torn wing edges and harsher dive posture.
- Minion ecology: Moth-raptor pack units should feel like nest juveniles, gliders, or carrion escorts shaped by the same reef storms.
- Asset priority notes: Keep the raptor skeleton legible under the moth influence; it should not become a pure insect.

## BASALT TYRANT

- Stage: Basalt Gate
- Horror frame: Hellgate Demon
- Runtime anchor: Prefab 7, subarchetype 3
- Core animal read: Volcanic siege toad and horned ape built into a living fortress beast.
- Real anatomy anchors: Gorilla forearm mass, cane-toad torso compression, ram horn rooting, kiln-lizard heat venting through the spine.
- Surface and materials: Black igneous slabs, glowing vent seams, blistered ash skin between plates, sulfur crust around elbows and mouth corners.
- Silhouette priority: Blocky crown, overbuilt arms, low center of gravity, vent-spine chimney line.
- Signature face details: Deep-set furnace eyes, horn bases merged into brow ridges, heavy underbite with cracked basalt teeth.
- Motion profile: Gatekeeper stance, short brutal rushes, walling shoulder checks, hammer-arm drops.
- Contamination signature: Sulfur furnace corrosives, slag particulate burden, and kiln-stiff matter tension that make the arena feel pressurized and choking.
- Phase escalation: Phase one is toll-keeper stillness, phase two opens more lava seams and arm spread, phase three reads hotter and more unstable with burst vents and collapsing armor edges.
- Minion ecology: Gate tithe brutes should feel like cinder-fed attendants bred in the same vents and toll corridors.
- Asset priority notes: Make it feel like a pressure-built geological animal, not a humanoid demon in rock armor.

## GOOLLOKI MOONFROG

- Stage: Bloom Pit
- Horror frame: Lunar Swamp Fever
- Runtime anchor: Prefab 8, subarchetype 1
- Core animal read: Giant swamp frog crossed with a brood toad and star-tracking nocturnal predator.
- Real anatomy anchors: Bullfrog jaw span, salamander spine flexibility, tree-frog toe articulation, crocodilian eye placement adjusted for an ambush amphibian.
- Surface and materials: Wet glandular skin, fungal pollen dusting, translucent throat sac veining, moon-ring eye membranes, algae-streaked back ridges.
- Silhouette priority: Huge crouched haunches, broad moon-round head, dangling throat mass, splayed grasping digits.
- Signature face details: Star-ring pupils, heavy upper lip, soft but predatory mouth line, luminous gland spots around the neck and shoulder pits.
- Motion profile: Suspended crouch, pulsing throat inflation, short explosive leaps, herd-like pressure through brood spawning and lung choke framing.
- Contamination signature: Pollen-slime toxicants, glandular breath saturation, and moon-fever hemoneural drift that make its swelling throat feel infectious.
- Phase escalation: Phase one watches and herds, phase two swells the throat and blooms more gland light, phase three reads feverish and overripe with heavier pulse, stretch, and mucous bloom.
- Minion ecology: Grub frogs should feel like larval or juvenile bloom-swamp feeders tied to its spawning cycle.
- Asset priority notes: Keep the amphibian weight and moisture convincing; the lunar traits should feel like a disease of the bog, not space magic.

## DUST ORACLE

- Stage: Dust Halo
- Horror frame: Occult Omen
- Runtime anchor: Prefab 5, subarchetype 2
- Core animal read: Carrion vulture and desert monitor reshaped into a ritual augur.
- Real anatomy anchors: Vulture neck length, lizard jaw hinge, ibex-like cranial crown geometry, insectile eye shielding only as a secondary detail.
- Surface and materials: Dust-caked hide, parchment-thin frills, cracked ritual pigments, loose sand shedding from every joint.
- Silhouette priority: Tall omen-neck, narrow chest, halo-like back fins or orbiting dust crest, long forelimb reach.
- Signature face details: Hooded prophet brow, bead-like multiple eye reflections under a dust veil, beak-jaw edges worn like ancient tools.
- Motion profile: Slow divining turns, range-peeling sidestep, sudden peck-thrust or omen lash, false stillness before attack.
- Contamination signature: Ritual dust inhalants, parchment-dry corrosive grit, and omen-driven neurochemical static that make stillness itself feel abrasive.
- Phase escalation: Phase one hides intent, phase two opens more frills and eye shine, phase three becomes a moving dust eclipse with harsher reach lines and less readable edges.
- Minion ecology: Omen eye harassers should feel like small scouting familiars, carrion augurs, or detached sensory brood.
- Asset priority notes: Prioritize prophetic dread and bone-dry realism over generic wizard-monster iconography.

## NIGHT ABYSS

- Stage: Black Tide
- Horror frame: Cosmic Abyss
- Runtime anchor: Prefab 6, subarchetype 3
- Core animal read: Pelagic deep-sea hunter with shore-crashing whale and angler anatomy.
- Real anatomy anchors: Sperm-whale forehead mass, gulper-eel jaw extension, shark caudal power, cephalopod softness in the throat and lower body transitions.
- Surface and materials: Oil-slick black skin, bioluminescent scar lines, surf foam trapped in pits, abyssal pressure scars around eye sockets and vents.
- Silhouette priority: Huge forehead or crown bulb, tapering tail darkness, too-wide mouth cut, broad surf-shadow body mass.
- Signature face details: Tiny abyss eyes, luminous lure scars or false-eye organs, mouth interior that reads deeper than the sprite should allow.
- Motion profile: Tide-led drift, undertow pull, sudden full-body lunge, wave-backed pressure rather than visible sprinting.
- Contamination signature: Black-surf oil toxicants, pressure-sick respiratory compression, and abyssal plasmic diffusion that make its silhouette feel chemically bottomless.
- Phase escalation: Phase one is unreadable tide bulk, phase two reveals more internal light and maw structure, phase three collapses the boundary between body and surf with more engulfing silhouette behavior.
- Minion ecology: Abyss drone tide units should look like pressure-adapted scavengers, lampfish, or brood parasites carried by the black surf.
- Asset priority notes: The creature should feel oceanically huge even when only part of it is visible.

## CROWN BEHEMOTH

- Stage: Crown Crater
- Horror frame: Regal Necromancy
- Runtime anchor: Prefab 8, subarchetype 3
- Core animal read: Ossified lion-bull monarch elevated into a grave-court titan.
- Real anatomy anchors: Bull neck and chest, lion forepaw authority, elephantine skull mass, stag-like crown spread only where it supports the royal silhouette.
- Surface and materials: Bone-plated regalia, grave-gold filigree fused to horn and shoulder, dried hide stretched over massive joints, funeral cloth remnants caught in armor spikes.
- Silhouette priority: Crown crest high above the skull, throne-wide shoulders, heavy chest depth, ceremonial tail or spinal pennant.
- Signature face details: Kingly forward brow, dead-socket jewels or ember eyes, blunt crushing muzzle lined with worn ceremonial teeth.
- Motion profile: Measured sovereign pacing, crushing step rhythm, throne-break lunges, deliberate claim of center space.
- Contamination signature: Grave-gold corrosive dust, embalming vapor burden, and royal bone-stasis chemistry that make the final arena feel entombed while still alive.
- Phase escalation: Phase one is command and judgment, phase two breaks the regalia and reveals old war-scars, phase three becomes a ruin-king in open collapse with more exposed bone and desperate grandeur.
- Minion ecology: Bone court elites should feel like embalmed retainers, ossuary knights, or half-resurrected vassals.
- Asset priority notes: It must read as the final ruler-beast of the campaign, not just the largest horned monster.

## Asset Pipeline Priorities

- First-pass sprite differentiation should focus on head shape, shoulder mass, limb logic, and posture before surface detailing.
- Second-pass detail should add biome-specific materials: barnacle, ash, bark, frost, crypt stone, glass, storm bloom, basalt, pollen slime, dust veil, oil-surf sheen, and necropolis bone.
- Animation tests should verify that each boss still reads correctly in idle, windup, hit-stun, recover, and phase-transition poses.
- Minion sheets should be revised in parallel so each boss encounter feels ecologically specific instead of sharing one generic creature language.
