from __future__ import annotations

import argparse
import json
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = ROOT / "concept_art_package"
ASSET_DIR = PACKAGE_DIR / "recraft_assets"
PAGE_DIR = PACKAGE_DIR / "pages"
PROFILE_MD = PACKAGE_DIR / "BANGO_PATOOT_WORLD_ENTITIES_PROFILE.md"
PROFILE_TXT = PACKAGE_DIR / "BANGO_PATOOT_WORLD_ENTITIES_PROFILE.txt"
MANIFEST_PATH = PACKAGE_DIR / "bango_patoot_concept_art_manifest.json"
PAGE_PLAN_PATH = PACKAGE_DIR / "bango_patoot_artbook_page_plan.json"
OUTPUT_BOOK = PACKAGE_DIR / "BangoPatoot_concept_artbook.ecbmps"
TITLE = "BANGO-PATOOT: UNDERHIVE NOCTURNE"
AUTHOR = "drIpTECH / GitHub Copilot"
PAGE_SIZE = (1600, 900)
ASSET_SIZE = (1344, 768)
UNITS_PER_IMAGE = 40


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("C:/Windows/Fonts") / "georgia.ttf",
        Path("C:/Windows/Fonts") / "arial.ttf",
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


FONT_TITLE = load_font("georgiab.ttf", 62)
FONT_SECTION = load_font("georgiab.ttf", 24)
FONT_HEADING = load_font("georgiab.ttf", 34)
FONT_BODY = load_font("segoeui.ttf", 24)
FONT_SMALL = load_font("segoeui.ttf", 20)
FONT_TINY = load_font("segoeui.ttf", 18)


DIALOGUE_MAP = {
    "cover_underhive_nocturne": [
        ("Bango", "If the city still remembers her, we can still reach her."),
        ("Patoot", "Then keep moving. The rails are whispering the way down."),
    ],
    "premise_duo_fantasy": [
        ("Tula Echo", "Follow the shrine heat, not the loudest hymn."),
    ],
    "duo_silhouette_language": [
        ("Bango", "You scout the ledges. I break the locks."),
        ("Patoot", "And when you miss a step, I keep you off the floor below."),
    ],
    "bango_anatomy_wardrobe": [
        ("Bango", "Every strap earns its keep. Nothing rides on me for show."),
    ],
    "patoot_anatomy_motion": [
        ("Patoot", "I do not fly away. I correct the fall."),
    ],
    "tula_memory_anchor": [
        ("Tula", "They can cage my body. They still cannot catalog my will."),
    ],
    "matra_vey_cyberwitch": [
        ("Matra Vey", "Mercy is the final obedience. I will make the city gentle by force."),
    ],
    "mother_comb_edda": [
        ("Edda", "A shrine is not a throne. It is a promise somebody keeps every day."),
    ],
    "vilm_siltcoat": [
        ("Vilm", "Maps cost extra when the walls start lying."),
    ],
    "sister_halceon": [
        ("Halceon", "I know the hymns they used to break us. I know where they skip a beat."),
    ],
    "apiary_junction_hub": [
        ("Patoot", "Warm lamps, clean ladders, three exits. This is where the city still breathes right."),
    ],
    "brassroot_borough": [
        ("Bango", "This was home before it became evidence."),
    ],
    "saint_voltage_arcade": [
        ("Patoot", "Everything here wants a prayer, a coin, or your nerves."),
    ],
    "ossuary_transit": [
        ("Bango", "They buried memory under the tracks and wondered why the rails howl."),
    ],
    "gutterwake_sewers": [
        ("Patoot", "Do not trust the bright water. It glows because it is hungry."),
    ],
    "cinder_tenements": [
        ("Bango", "A house should hold a family. Not a sermon with teeth."),
    ],
    "aviary_last_broadcast": [
        ("Patoot", "Wind is honest. The speakers are what twist it."),
    ],
    "witchcoil_spire": [
        ("Matra Vey", "One city, one will, one perfect hush."),
    ],
    "shrine_reliquaries": [
        ("Edda", "Repair first. Blessing comes after the bolts hold."),
    ],
    "hive_sigils_pollen": [
        ("Vilm", "Tiny things move districts. That is why everyone kills over them."),
    ],
    "lantern_kin_rescues": [
        ("Lantern Kin", "We kept the light small so the dark would think we were gone."),
    ],
    "traversal_kit": [
        ("Patoot", "Grab the rail late. Jump early. Trust me in the middle."),
    ],
    "combat_stance_language": [
        ("Bango", "Commit to the hit. Survive the answer."),
    ],
    "egosphere_relationship_web": [
        ("Tula Echo", "People leave marks in each other long before the city writes them down."),
    ],
    "honey_debt_collector": [
        ("Debt Collector", "If the borough cannot pay in coin, it will pay in shrine metal."),
    ],
    "bishop_static": [
        ("Bishop Static", "A louder miracle is still a miracle to those who cannot leave."),
    ],
    "railmouth_ossivar": [
        ("Patoot", "Listen. The station beast announces every charge like a train that hates us."),
    ],
    "maw_of_silt": [
        ("Bango", "No eyes. No mercy. Just appetite and runoff."),
    ],
    "caretaker_red_mother": [
        ("Red Mother", "Be still, little lights. I can love you into silence."),
    ],
    "broadcast_harrower": [
        ("Patoot", "Cut the pattern. Do not fight the scream head-on."),
    ],
    "matra_vey_ascendant": [
        ("Matra Vey", "I gave the city one throat so it would never disagree again."),
    ],
    "three_ds_exploration_mockup": [
        ("Patoot", "Landmark ahead. Shrine left. Trouble above."),
    ],
    "three_ds_ui_mockup": [
        ("Bango", "Good. Put the warnings where my hands can find them."),
    ],
    "closure_rear_cover": [
        ("Tula", "It is still wounded. That means it is still alive enough to heal."),
    ],
}


OVERLAY_MAP = {
    "cover_underhive_nocturne": ["Brassroot descent route", "Shrine heat below"],
    "premise_duo_fantasy": ["Duo traversal covenant", "Rescue motive"],
    "duo_silhouette_language": ["Idle / alert / leap / guard", "Top-screen readability test"],
    "bango_anatomy_wardrobe": ["Field harness logic", "Ward-ready silhouette"],
    "patoot_anatomy_motion": ["Perch balance", "Glide correction anatomy"],
    "tula_memory_anchor": ["Echo-state continuity", "Captivity does not erase agency"],
    "matra_vey_cyberwitch": ["Obedience-engine interface", "Caretaker tyranny"],
    "apiary_junction_hub": ["Service hub", "Shrine / vendor / route legibility"],
    "brassroot_borough": ["Opening district", "Warmth under pressure"],
    "saint_voltage_arcade": ["Coin-fed worship grid"],
    "ossuary_transit": ["Memorial rail geometry"],
    "gutterwake_sewers": ["Runoff logic", "Ambush fog rhythm"],
    "cinder_tenements": ["Domestic horror threshold"],
    "aviary_last_broadcast": ["Wind-ladder route test"],
    "witchcoil_spire": ["Final ascent landmark chain"],
    "district_material_bible": ["Comb-metal / wax / brick / fungus"],
    "lighting_color_script": ["Purification state drift", "Faction-owned light"],
    "shrine_reliquaries": ["Rest / refine / recover"],
    "hive_sigils_pollen": ["Macro progression tokens"],
    "lantern_kin_rescues": ["Safety language"],
    "notes_scraps_codex": ["Paper trail worldbuilding"],
    "traversal_kit": ["Route memory verbs"],
    "combat_stance_language": ["Heavy / cut / interrupt"],
    "move_catalog_taxonomy": ["1000-slot move grammar"],
    "egosphere_relationship_web": ["Trust / debt / fear web"],
    "three_ds_exploration_mockup": ["HUD-safe focal path"],
    "three_ds_ui_mockup": ["Bottom-screen systems stack"],
    "appendix_glossary_archive": ["Reference archive"],
    "legal_publication_plate": ["Internal publication plate"],
    "closure_rear_cover": ["Bittersweet recovery state"],
}


def spread(
    index: int,
    slug: str,
    title: str,
    section: str,
    subject: str,
    setting: str,
    focus: str,
    palette: str,
    world_role: str,
    gameplay_role: str,
    visual_directive: str,
    mode: str = "standard",
) -> dict:
    return {
        "index": index,
        "slug": slug,
        "title": title,
        "section": section,
        "subject": subject,
        "setting": setting,
        "focus": focus,
        "palette": palette,
        "world_role": world_role,
        "gameplay_role": gameplay_role,
        "visual_directive": visual_directive,
        "mode": mode,
    }


SPREADS = [
    spread(1, "cover_underhive_nocturne", "Underhive Nocturne", "Cover / Orientation", "Bango-Patoot key art centered on Bango and Patoot descending a shrine-lit undercity vista", "the vertical city-body of Brassroot, hive lanterns, rail ribs, chapel steel, fog wells, and Witchcoil silhouettes", "heroic cover illustration with clean title space, high legibility, and a premium concept artbook front cover composition", "honey amber, shrine ivory, oxidized brass, bruise violet, soot black", "This image establishes the full tone of the project: folk-horror, industrial devotion, and a duo bond moving downward into a city that behaves like a living organism.", "It sets the visual benchmark for every later district, faction, and character plate, and it acts as the book's anchor image.", "Keep the duo readable at a distance, give the city strong vertical depth, and make the religious-industrial silhouettes feel original rather than borrowed.", "cover_toc"),
    spread(2, "premise_duo_fantasy", "Core Premise And Duo Fantasy", "Introduction", "Bango and Patoot as an inseparable traversal-and-combat pair", "Apiary Junction opening overlook with shrine rails, worker lifts, signal combs, and ritual smoke", "frontispiece illustration that explains the player fantasy through pose, scale, and movement intent", "warm apiary gold, fungal green, soot slate, ritual red", "This spread frames the game as a rescue-driven collectathon action-RPG rather than parody or pastiche, with companionship and sensory intelligence at its center.", "It should imply that traversal, combat, shrine refinement, and social state all emerge from the duo relationship.", "Stage Bango as grounded and stubborn, Patoot as sharp and agile, and make the environment feel like a route network waiting to be explored.", "intro_art"),
    spread(3, "duo_silhouette_language", "Duo Silhouette Language", "Heroes", "Bango and Patoot seen in multiple relationship poses and traversal stances", "a neutral shrine practice chamber lined with embossed comb-metal and chalk route diagrams", "silhouette language sheet showing idle, alert, mounted-assist, leap, and combat-read poses", "bone ivory, rail brass, hive orange, storm blue", "This sheet defines how the pair read from a distance across every district and every gameplay state.", "It informs animation blocking, camera composition, box art, and NPC readability during hectic exploration scenes.", "Preserve asymmetric harmony: Bango broad and rooted, Patoot narrow and cutting, both visibly dependent on one another.") ,
    spread(4, "bango_anatomy_wardrobe", "Bango Anatomy And Wardrobe", "Heroes", "Bango as a horned tunnel-born ursine survivor with ritual field gear", "Apiary maintenance workshop table, hand-forged hooks, hive cloth, dented reliquary metal", "full character design sheet covering anatomy, costume layers, horn structure, gloves, boots, satchel, and ward harness", "earth umber, shrine linen, brass oxide, ember orange", "Bango must feel prehistoric and urban at once: a body shaped by tunnels, labor, and shrine duty rather than polished hero fantasy.", "His outfit carries gameplay information about durability, climbing, carrying capacity, and shrine interaction without becoming overdesigned.", "Favor tactile materials, practical tailoring, and memorable horns that read cleanly on the 3DS top screen.") ,
    spread(5, "patoot_anatomy_motion", "Patoot Anatomy And Motion", "Heroes", "Patoot as a reptile-dodo-ostrid companion with ritual tack and scout gear", "aviary roost scaffolds, hanging charms, cable perches, wind streamers", "companion anatomy sheet emphasizing gait, perch logic, wing-assisted glide posture, beak utility, and saddle-adjacent mounting zones", "ash teal, feather charcoal, saddle tan, signal amber", "Patoot is not comic relief; Patoot is an adaptive intelligence engine that extends Bango's movement, awareness, and emotional calibration.", "The design must support scout calls, peck switches, glide correction, and affectionate body language without turning Patoot into a generic bird mount.", "Keep the skull and leg structure unusual but readable, with strong side-profile beak shape and credible perch behavior.") ,
    spread(6, "tula_memory_anchor", "Tula The Memory Anchor", "Heroes", "Tula as hive-keeper apprentice, chant archivist, and captured sister", "memory room reliquary lit by reflected wax, pollen jars, and hymn cylinders", "portrait and costume sheet showing Tula in free state, captivity echoes, and sabotage mode inside the Witchcoil lattice", "wax cream, copper red, ash blue, hive gold", "Tula is the emotional hinge of the narrative and the proof that undercity ritual knowledge can resist industrial control.", "Her visual language has to bridge domestic tenderness, civic duty, and psychic resilience so that her echoes carry real narrative weight.", "Show calm competence, not fragility; the capture event changes her circumstances, not her agency.") ,
    spread(7, "matra_vey_cyberwitch", "Matra Vey The Cyberwitch", "Antagonists", "Matra Vey as ritual engineer, caretaker tyrant, and city-body theologian", "Witchcoil laboratory nave with choir drones, memory spears, and rotating shrine fragments", "villain design plate covering base form, broadcast harness, hymn-engine interface, and ascendant silhouette", "surgical silver, ritual violet, arterial red, cathedral black", "Matra Vey must read as a totalizing caretaker whose solution abolishes consent, not as random evil.", "Her costume and machinery need to merge chapel doctrine, broadcast infrastructure, and surgical precision into one instantly recognizable antagonist image.", "Keep the silhouette elegant, vertical, and coercively nurturing; avoid generic dark-sorceress shorthand.") ,
    spread(8, "mother_comb_edda", "Mother Comb Edda", "Allies", "Mother Comb Edda as the first shrine-keeper and civic memory elder", "first apiary reliquary with honey lamps, civic offerings, and patched worker banners", "mentor portrait and ritual-service design showing shrine tools, posture language, and elder authority", "hive amber, smoke brown, linen white, brass green", "Edda embodies the city's older ethics: stewardship, mutual aid, and ritual as community maintenance rather than hierarchy.", "She frames shrine refinement as care work, which gives systemic actions moral and social meaning.", "Present her as worn but formidable, with strong hands, layered garments, and a face shaped by work rather than mystic abstraction.") ,
    spread(9, "vilm_siltcoat", "Vilm Siltcoat", "Allies", "Vilm Siltcoat as salvage broker, tunnel fixer, and map-for-hire pragmatist", "back-alley salvage stall stacked with wires, comb-metal, elevator teeth, and relic scrap", "merchant character design with portable stall kit, rope rigging, chalk maps, and route-marking tools", "oil blue, rust orange, lamp yellow, tar black", "Vilm grounds the game's economy in actual city labor and black-market logistics.", "He contextualizes gear upgrades, hidden maintenance routes, and the uneasy overlap between survival and opportunism.", "Keep him sly, mobile, and materially specific; his props should be as informative as his body language.") ,
    spread(10, "sister_halceon", "Sister Halceon", "Allies", "Sister Halceon as ex-enforcer penitent carrying chapel doctrine scars", "defector prayer cell with stripped icon frames, confession vents, and copied hymn tapes", "character portrait contrasting former chapel enforcement gear with present-day penitential modifications", "chalk white, bruise plum, iron grey, votive blue", "Halceon bridges the institutional history of the city and the player's gradual understanding of the machine-cults.", "She is the human face of doctrinal damage, repentance, and selective complicity.", "Her costume should show subtraction, repurposing, and visible self-editing rather than a simple faction color swap.") ,
    spread(11, "apiary_junction_hub", "Apiary Junction", "Districts", "Apiary Junction as the layered shrine-and-merchant hub at the center of the city", "interlocked plaza of reliquary bridges, worker lifts, pollen boilers, and bulletin niches", "hub environment key art with strong route readability and clear service zones for shrine, vendors, and memory rooms", "honey gold, coal blue, shrine white, wet stone grey", "Apiary Junction is where the game teaches the player that every systemic action feeds back into civic texture and faction response.", "It needs to feel lived in, navigable, and expandable as later acts restore more of the fast-travel lattice.", "Compose the hub so each landmark is memorable from the 3DS camera while still feeling like one interlocked body.") ,
    spread(12, "brassroot_borough", "Brassroot Borough", "Districts", "Brassroot Borough as the opening worker district and site of the hushfall kidnapping", "tenements, rooftop laundries, steam pipes, shrines, and public feast lanes built over old service tunnels", "district establishing shot focused on social warmth under threat, showing the place before and after ritual corruption", "warm hive gold, brick umber, steam grey, blackout violet", "Brassroot must sell what is being lost when the game begins: neighborhood ritual, worker improvisation, and the tenderness of shared civic habits.", "As the opening district, it teaches shrine loops, rescue chains, and route memory through approachable but dense urban layout.", "Balance comfort and foreboding; the district should feel beloved before it feels endangered.") ,
    spread(13, "saint_voltage_arcade", "Saint Voltage Arcade", "Districts", "Saint Voltage Arcade as neon chapel-market hybrid, indulgence district, and gang-lit miracle mall", "arcade cabinets, votive kiosks, chapel wiring, market bridges, and prayer-fee machines", "district environment painting emphasizing sensory overload, commerce, and corrupted worship infrastructure", "neon cyan, sodium magenta, brass gold, confession black", "Saint Voltage is where the game reveals that devotion, entertainment, and predation now share the same circuitry.", "It supports lateral route exploration, social-state play, and faction contrast between merchants, defectors, and chapel remnants.", "Make it loud without losing readability; surfaces should stay coherent even as signage and light stacks multiply.") ,
    spread(14, "ossuary_transit", "Ossuary Transit", "Districts", "Ossuary Transit as rail backbone, memorial vault, and hidden dead-route archive", "bone furnaces, switchyards, memorial arches, and derelict rail platforms descending into burial infrastructure", "district key art showing rail geometry, memorial massing, and traversal across dead civic machinery", "bone ivory, furnace amber, soot black, oxidized iron", "Ossuary Transit makes the buried social history of the city literal by revealing how forgotten communities were folded into infrastructure.", "It introduces heavier traversal logic through trains, switch timing, and long-sightline landmark memory.", "Keep the architecture ceremonial and industrial at once, with bone motifs integrated into believable transit construction.") ,
    spread(15, "gutterwake_sewers", "Gutterwake Sewers", "Districts", "Gutterwake as fungal runoff maze, floodgate machine, and chemical honey sump", "sluice wheels, drowned workshops, rope catwalks, fungus combs, and cryptid nests", "humid underworld environment painting built around water logic, visibility rhythm, and ambush layering", "mold green, chemical amber, wet steel, midnight blue", "Gutterwake is the district where environmental contamination becomes a legible villainous process instead of pure background mood.", "It uses vertical scouting, water hazards, and floodgate purification to make Patoot especially central to play.", "Let the moisture, fungus, and runoff all have different material identities so the space feels engineered rather than randomly slimy.") ,
    spread(16, "cinder_tenements", "Cinder Tenements", "Districts", "Cinder Tenements as the apartment-chapel district where domestic horror becomes explicit", "stairwells, burnt kitchens, nursery shrines, confession vents, and soot-heavy living blocks", "district hero shot focused on homes converted into cult architecture and the cost borne by ordinary households", "ash white, nursery red, soot black, lamp gold", "Cinder Tenements is the game's emotional center because it converts doctrine into everyday pressure inside homes and child spaces.", "Its layouts should emphasize rescue, witness, and room-to-room story discovery rather than large plazas.", "Make apartments intimate and specific; every doorway should imply a life, not just a level module.") ,
    spread(17, "aviary_last_broadcast", "Aviary Of The Last Broadcast", "Districts", "Aviary district built from masts, cages, signal decks, cable bridges, and public address chambers", "wind ladders, speaker arrays, aerial cages, and sheer drop shafts", "vertical traversal showcase environment with strong sense of altitude, wind exposure, and broadcast reach", "storm white, signal blue, cable black, rust brass", "The Aviary is where the game fully cashes in Patoot's aerial readability and the city's obsession with mass instruction.", "It should feel liberating and dangerous at once, with thin routes, open voids, and views across the whole wounded city.", "Use negative space aggressively so every perch and ladder becomes meaningful.") ,
    spread(18, "witchcoil_spire", "Witchcoil Spire", "Districts", "Witchcoil Spire as final ritual factory combining chapel steel, hive geometry, organ pipes, and obedience machinery", "sacrifice lifts, choir cores, memory lattices, and comb-like vertical chambers", "final district concept with cathedral dread, machine precision, and cumulative motif payoff from the whole game", "ritual violet, furnace orange, ivory ash, arterial red", "The Spire is where every prior district language fuses into one horrifyingly coherent worldview.", "It must feel like the city has become conscious of itself as machinery and theology at the same time.", "Build vertical depth and repeating geometry without losing landmark recognition for final ascent gameplay.") ,
    spread(19, "district_material_bible", "District Material Bible", "World Language", "materials, trims, masonry, cloth, wax, comb-metal, cable, glass, and fungal intrusion states", "a curated board of swatches, fragment studies, and architectural cutaways from all seven districts", "material study sheet that standardizes how surfaces age, corrode, sanctify, and become contaminated", "wax cream, green brass, tar black, damp brick, fungal teal", "This board keeps the project visually coherent by establishing what each district is literally made from and how sacred versus industrial wear appears.", "It is essential for environment outsourcing, prop consistency, and later texture memory on constrained hardware.", "Favor material storytelling over generic mood swatches; every sample should imply labor history or ritual use.") ,
    spread(20, "lighting_color_script", "Lighting And Color Script", "World Language", "the full Bango-Patoot lighting progression from borough warmth to spire coercion", "a cinematic strip of district key lights, practical sources, fog values, and shrine-state transitions", "color script board mapping emotional cadence, purification shifts, and faction-controlled lighting behavior", "apiary gold, neon chapel cyan, ossuary ember, sewer acid, spire violet", "The color script is how the game communicates emotional state and civic corruption before the player reads a single line of dialogue.", "It supports route memory, threat telegraphing, and the before-after transformation of purified districts.", "Keep the palette original and stateful; changes must feel systemic, not merely decorative.") ,
    spread(21, "shrine_reliquaries", "Shrine Reliquaries", "Systems", "apiary shrines as civic service nodes, rest points, and refinement chambers", "wax altars, honey boilers, catalyst trays, faction offerings, and route boards", "hero prop-and-space study covering shrine silhouettes, states of repair, and interaction affordances", "shrine gold, ceramic white, soot bronze, herbal green", "Shrines are the structural heart of the game and need to feel like practical public infrastructure infused with devotion.", "They govern healing, fast travel, build refinement, social-state updates, and narrative pacing.", "Show serviceability, repair seams, and community use; they are not untouchable monuments.") ,
    spread(22, "hive_sigils_pollen", "Hive Sigils And Shrine Pollen", "Systems", "macro progression collectibles, catalyst matter, and ritual repair tokens", "cabinet drawers, comb cases, wax tablets, and pollen sieves used by shrine keepers", "collectible sheet illustrating scale, state rarity, and storage logic for core progression resources", "amber honey, parchment cream, pollen yellow, brass brown", "These objects translate exploration into civic restoration and build growth, so their design must feel materially important.", "They appear repeatedly on the UI, in shrines, in reward moments, and in faction economies.", "Make each class of collectible easy to distinguish by silhouette before color or text is applied.") ,
    spread(23, "lantern_kin_rescues", "Lantern Kin", "Systems", "rescued hive-children and their small ritual equipment", "temporary safe rooms, lantern caches, chalk nests, and route-hide niches inside districts", "rescue-focused concept page showing child silhouettes, lantern types, and the visual language of safety in a dangerous city", "warm wax gold, blanket blue, soot plum, lantern orange", "Lantern Kin rescues are how the game keeps the stakes human and local while progressing a larger city-scale conflict.", "Their presence should visibly improve shrine warmth, social hubs, and certain district states after rescue chains complete.", "Avoid generic cute mascots; they are vulnerable people first, symbolic lights second.") ,
    spread(24, "notes_scraps_codex", "Nocturne Notes And Choir Scraps", "Systems", "currency notes, doctrine scraps, hymn cartridges, and codex evidence items", "archive drawers, market bundles, and confession booth caches", "document-and-currency sheet that defines the collectible paper trail of the city", "ink black, vellum cream, wax red, cartridge brass", "These items connect exploration to lore, upgrade pacing, and the feeling that the city keeps records of everything it harms.", "They should visually bridge salvage economy, shrine memory, and enemy ideology.", "Use believable print, stamp, and wear logic even though final generation must not include actual readable text.") ,
    spread(25, "traversal_kit", "Traversal Kit", "Systems", "Bango and Patoot traversal actions as a unified movement language", "practice routes across apiary chains, ladders, rails, glides, shrine grapples, and drop-hover wells", "move-development board showing jump arcs, ledge grabs, perch assists, rail grinds, and route-solving posture beats", "brass gold, sky teal, stone grey, signal red", "Traversal is the project's signature feel and must communicate weight, cleverness, and partnership.", "Every unlocked traversal verb should create new route readings in old districts, not simply faster motion.", "The page should feel like a designer's movement bible with clear action clarity at a glance.") ,
    spread(26, "combat_stance_language", "Combat Stance Language", "Systems", "Bango and Patoot stance families, guard silhouettes, dodge shapes, and ward casts", "combat pit reliquary marked with training sigils and contact lines", "combat posture sheet expressing close-quarters positional play rather than musou spectacle", "blood orange, iron grey, shrine gold, shadow blue", "The combat stance language has to sell that Bango is heavy and committed while Patoot adds interrupts, scouts, and pressure windows.", "It also needs to support a large procedural move catalog without losing frame clarity.", "Keep every stance readable from the top screen and distinct under low-contrast district lighting.") ,
    spread(27, "move_catalog_taxonomy", "Move Catalog Taxonomy", "Systems", "the procedural 1000-slot move catalog represented as design clusters and tag families", "chalk board, filing drawers, shrine matrix diagrams, and move cards pinned into stance networks", "systems visualization sheet translating a huge move set into a readable taxonomy for designers and artists", "chalk white, patent black, ember orange, muted jade", "The move catalog is not just content volume; it is the rules grammar that ties stance, locomotion, angle, utility tags, and ward modifiers together.", "A clear taxonomy lets future asset production scale without visual or systemic drift.", "Treat the board as a practical dev artifact, not abstract UI art.") ,
    spread(28, "egosphere_relationship_web", "EgoSphere Relationship Web", "Systems", "relationship network of trust, debt, fear, respect, mimicry, and rivalry across key non-player entities", "a shrine notice wall layered with cords, icons, debt tabs, and memory tokens", "social-systems visualization that makes Bango-Patoot's NPE logic legible through analog civic artifacts", "wax red, string ivory, brass gold, soot black", "EgoSphere logic determines prices, ambush warnings, rumor access, and district mood shifts, so it must feel embedded in the city rather than abstract menus.", "This spread defines the visual language for social telemetry and consequence tracking.", "Favor tactile relationship mapping over digital diagrams; the city records people physically.") ,
    spread(29, "shrine_keepers_faction", "Shrine Keepers", "Factions", "the network of apiary wardens, honey stewards, and memory caretakers who preserve civic ritual", "shrine service halls, offering carts, repair benches, and community kitchens", "faction style sheet covering garments, tools, insignia, and service architecture", "wax gold, linen white, ash blue, brass patina", "The shrine keepers embody restorative mutuality and the pre-industrial ethics the city is in danger of losing.", "Their design language should shape upgrades, sanctuary spaces, and many of the game's trust-based side quests.", "Keep them practical and municipal, not monastic fantasy priests.") ,
    spread(30, "salvage_brokers_faction", "Salvage Brokers", "Factions", "salvage crews, route fixers, gear traders, and tunnel opportunists", "market rigging, hoist carts, cable nests, and scrapped machine altars", "faction board focusing on silhouettes, barter tools, and mobile stall architecture", "oil blue, rust orange, steel grey, headlamp yellow", "The salvage brokers are the city's practical survivalists, morally elastic but deeply competent.", "They are essential for gear economies, hidden maintenance paths, and mid-layer social politics.", "Let their equipment feel modular and repaired, with every piece telling a story of reuse.") ,
    spread(31, "chapel_defectors_faction", "Chapel Defectors", "Factions", "ex-preachers, choir techs, and wardens who broke from the obedience engine", "hidden confession rooms, stripped lecterns, patched doctrine archives, and improvised shelters", "faction look sheet emphasizing subtraction, contraband scripture, and half-erased insignia", "plaster white, faded plum, brass smoke, ink black", "The defectors are living evidence that institutions can wound and still be resisted from within.", "They mediate lore delivery, stealth support, and morally difficult quest lines.", "Build them out of remnants, penance, and visible compromise rather than clean rebellion aesthetics.") ,
    spread(32, "borough_gangs_faction", "Borough Gangs", "Factions", "street debt crews, extortionists, shrine scrappers, and feast-line predators", "narrow alleys, patched armor, improvised banners, tally ledgers, and stolen shrine parts", "faction sheet defining gang silhouettes, debt brands, tools, and neighborhood-specific swagger", "tar black, hazard yellow, sickly red, alley sodium", "The borough gangs are not elegant villains; they are the city's everyday predation made organized.", "They supply recurring enemy types, localized social pressure, and the feeling that collapse breeds opportunistic rule.", "Give them function-first gear and place-based variation so they feel like actual street ecologies.") ,
    spread(33, "honey_debt_collector", "Honey Debt Collector", "Bosses", "opening district boss built from shrine scrap, tally chains, and extortion ceremony", "Brassroot debt hall, melted reliquary parts, chained ledger hooks, and feast debris", "boss key art emphasizing heavy silhouette, collection rituals, and worker-neighborhood menace", "rust gold, debt red, soot black, hive amber", "This boss teaches that violence in Bango-Patoot often emerges from economic exploitation before it becomes openly cultic.", "Mechanically it introduces readable windup, pressure lanes, and shrine-part salvage as threat language.", "Make the shape oppressive but human enough to feel plausible inside the borough.") ,
    spread(34, "bishop_static", "Bishop Static", "Bosses", "slot-machine choir pulpit bishop fused to neon chapel hardware", "Saint Voltage pulpit stage with miracle screens, cable organs, and paid indulgence kiosks", "boss illustration focused on broadcast glare, coin-fed ritual machinery, and predatory spectacle", "neon cyan, chapel magenta, chrome brass, sermon black", "Bishop Static is where the game fully merges worship and monetized stimulation into one grotesque body.", "The fight grammar should be legible from color, screen stacks, and choir drone orbit patterns.", "Aim for unnerving charisma instead of random monster chaos.") ,
    spread(35, "railmouth_ossivar", "Railmouth Ossivar", "Bosses", "ossified signal-engine beast made from memorial bones and transit hardware", "Ossuary switchyard vaulted beneath memorial bells and furnace smoke", "boss key art showing rail jaws, signal horns, and bell-like bone structure", "furnace amber, bone ivory, signal red, ash grey", "Ossivar turns the transit system into a predator and makes buried history physically hostile.", "Its visual logic should support charge lines, switch timing, and arena route memory.", "Keep the body architecture modular enough to imply it was built out of many civic dead.") ,
    spread(36, "maw_of_silt", "Maw-Of-Silt", "Bosses", "blind sewer cryptid swollen by chemical honey and runoff sacrament", "Gutterwake sump cathedral of floodgates, fungus rafts, and drowned pipes", "boss art built around smellable sludge weight, blind hunting behavior, and sluice-wheel scale", "acid amber, mold green, tar black, wet steel", "Maw-of-Silt is the consequence of industrial contamination rendered as appetite and mass.", "The fight uses water state, flow timing, and aerial scouting to keep the player reading the arena.", "Avoid generic slime-monster shorthand; anchor it in sewers, cryptid folklore, and industrial runoff.") ,
    spread(37, "caretaker_red_mother", "Caretaker Red Mother", "Bosses", "cult matron who turns nursery machinery and soot dolls into an obedience ritual", "Cinder Tenements nursery-chapel packed with cradles, soot dolls, and hymn cranks", "boss key art emphasizing maternal coercion, domestic machinery, and ritualized care turned violent", "nursery red, ash white, soot black, candle gold", "Red Mother is the emotional horror peak because she demonstrates how care language can be weaponized inside homes.", "The fight should feel intimate, spatially layered, and morally revolting without needing gore.", "Keep every prop sourced from domestic life and child maintenance, then push it into ritual function.") ,
    spread(38, "broadcast_harrower", "Broadcast Harrower", "Bosses", "stitched flock-machine that weaponizes signal patterns and public-address frenzy", "Aviary signal deck with cages, speaker horns, storm cables, and wind sheer", "boss painting focused on aerial menace, sonic geometry, and stitched avian machinery", "storm white, cobalt blue, rust brass, scream black", "The Harrower is the clearest articulation of broadcast as possession and crowd control.", "Its visuals must support rhythm-reading, dodge timing, and counter-hymn payoff.", "Keep the form avian and mechanical in equal measure; it should never read as a simple robot bird.") ,
    spread(39, "matra_vey_ascendant", "Matra Vey Ascendant", "Bosses", "final fused state of Matra Vey with the obedience lattice and exposed harmony anchors", "Witchcoil apex chamber where shrine fragments, organ pipes, and city arteries converge", "final boss apocalypse concept showing anchor targets, ritual body scale, and city-body integration", "violet lightning, blood ember, shrine ivory, abyss black", "The ascendant form must feel like the city itself is trying to become one obedient organism.", "This spread defines the climax of the whole visual language and the pattern-reading victory condition.", "Preserve identifiable traces of Matra Vey inside the larger machine-body so the fight remains personal.") ,
    spread(40, "lantern_apiary_fauna", "Lantern Apiary Fauna", "Bestiary", "supportive and ambient creatures tied to shrine ecologies, hives, and lantern networks", "apiary rafters, pollen gardens, honey vents, and worker rooftops", "fauna board illustrating helper beetles, comb moths, ember bees, and route-marking lantern swifts", "amber gold, moss green, soot brown, soft cream", "These creatures are how the world feels inhabited by more than enemies and quest givers.", "They communicate district health, shrine purification, and the possibility of cooperative city life.", "Keep them functional and symbolic, with believable ecological niches in the underhive.") ,
    spread(41, "sewer_cryptids_utility_vermin", "Sewer Cryptids And Utility Vermin", "Bestiary", "hostile and ambient underworks creatures shaped by runoff, neglect, and folklore", "Gutterwake culverts, sump vents, abandoned service nests, and flood cavities", "bestiary page defining rat-otter scavengers, pipe eels, fungus hounds, and drainage saints gone feral", "mold green, wet steel, bruise blue, rust orange", "This group supplies district texture, threat layering, and local storytelling in routes between major encounters.", "They should feel native to infrastructure instead of imported fantasy monsters.", "Build every creature around a specific maintenance niche, failure state, or folk belief.") ,
    spread(42, "underhive_vehicles_liftways", "Underhive Vehicles And Liftways", "Props", "cage lifts, maintenance sleds, honey tram wagons, sermon wagons, and rail shunts", "transit depots, lift shafts, service gantries, and shrine cargo docks", "vehicle concept board that links mobility, labor, and district identity across the city", "steel grey, brass gold, tar black, lamp amber", "Vehicles and liftways make the city feel industrially alive and help explain how children, goods, and doctrine are moved.", "They are traversal supports, environmental storytelling props, and faction signifiers.", "Keep them repairable and mechanical, never sleek or science-fiction generic.") ,
    spread(43, "ritual_tools_reliquary_kit", "Ritual Tools", "Props", "field kit of shrine maintenance tools, counter-ritual supplies, and domestic ward objects", "Edda's workbench covered in wax tabs, honey knives, ash brushes, and ward chalk", "hero prop spread for close-up item design and inventory silhouette clarity", "wax cream, brass gold, char black, herb green", "The ritual kit is how the player reads the game as practical civic mysticism instead of flashy spellcasting.", "It ties together progression systems, puzzle solving, and character identity.", "Each item should appear useful, hand-maintained, and plausible in both shrine and household contexts.") ,
    spread(44, "street_furnishings_kiosks", "Street Furnishings And Merchant Kiosks", "Props", "district furniture kit including benches, fee boxes, route boards, vending shrines, and broker kiosks", "Apiary Junction, Voltage markets, borough corners, and tenement service landings", "prop bible for world dressing, memory landmarks, and vendor readability", "brick brown, brass green, soot black, poster cream", "Street furnishings are the connective tissue that make districts feel civic rather than purely level-designed.", "They support wayfinding, social tone, and player memory of routes and hubs.", "Make them modular and district-specific, with recurring structural logic across the whole city.") ,
    spread(45, "signage_glyphs_wayfinding", "Signage, Glyphs, And Wayfinding", "Props", "district signs, shrine glyphs, debt marks, route arrows, hymn seals, and faction tags", "notice walls, lift thresholds, market archways, and chapel corridors", "wayfinding sheet defining icon grammar for the undercity's physical information systems", "chalk white, warning red, brass gold, tar black", "A strong glyph system is essential for both world coherency and hardware readability on 3DS.", "It lets the city communicate history, danger, ownership, and ritual permission without overreliance on text.", "Design for fast recognition, analog wear, and cross-district evolution.") ,
    spread(46, "three_ds_exploration_mockup", "3DS Top-Screen Exploration Mockup", "Presentation", "representative exploration scene rendered as if viewed on the 3DS top screen", "Apiary Junction to Brassroot route with Bango, Patoot, HUD-safe focal silhouettes, and layered parallax depth", "presentation key art translating the visual bible into actual handheld framing and readability constraints", "hive gold, soot blue, brass white, fungus green", "This mockup proves the concept art package can survive translation into the target platform's camera and screen hierarchy.", "It should balance atmosphere with game-readable silhouettes, route lines, and focal depth.", "Compose for stereoscopic suggestion and strong landmark spacing, not just poster beauty.") ,
    spread(47, "three_ds_ui_mockup", "3DS Bottom-Screen Systems UI", "Presentation", "bottom-screen interface showing shrine stats, relationship telemetry, map hints, and Patoot support prompts", "a stylized mock handheld composite with tactile buttons, codex tabs, and route widgets", "UI concept sheet for menus, telemetry panels, and collectible tracking on the lower screen", "wax cream, brass gold, ink black, signal teal", "The UI must make the dense systemic game legible without feeling sterile or disconnected from the world's material language.", "This spread defines how shrine logic, EgoSphere values, inventory, and route information can coexist cleanly on hardware.", "Favor analog decorative cues anchored in shrine and salvage aesthetics over generic fantasy HUD chrome.") ,
    spread(48, "appendix_glossary_archive", "Appendix And Glossary Archive", "Appendix", "an archival layout of maps, callouts, heraldry, and reference drawers for the whole project", "sealed library drawers, route folios, memory cards, and shrine catalog binders", "supplementary appendix-art background supporting reference pages and glossary content", "vellum cream, brass gold, ledger red, archive umber", "This spread closes the main design run with a more documentary tone, signaling that the book now enters reference material and terminology.", "It supports the final utility pages without breaking aesthetic continuity.", "Keep it archival and elegant, with strong negative space for dense text overlays.", "appendix_glossary"),
    spread(49, "legal_publication_plate", "Legal And Publication Plate", "Publication", "publication-endpaper style page with shrine seal, copyright framing, and civic archive ornament", "clean publication desk scene with wax seal, printed plates, and a final stamped ownership mark", "formal art background for legal, copyright, publication, and closing summary matter", "ivory parchment, wax red, iron black, subdued gold", "This spread must feel official and clean while still belonging to the underhive civic world rather than a real-world corporate template.", "It gives the package a finished publication identity suitable for ECBMPS compilation and review.", "Avoid real logos and preserve original-property framing throughout.", "legal_epilogue"),
    spread(50, "closure_rear_cover", "Final Closure", "Closure", "a quiet post-ritual city vista showing recovery, ambiguity, and the possibility of civic tending", "dawn over Apiary Junction and distant districts, with repaired lights, smoke drift, and the Witchcoil scar still visible", "final closure illustration and rear-cover key art pair that summarize hope without pretending the city is fully healed", "dawn amber, cold slate, shrine white, bruise violet", "The final image should echo the cover while proving that the city can be read, tended, and slowly restored after catastrophe.", "It functions both as the emotional goodbye page and the rear-cover visual identity for the package.", "Keep the mood bittersweet and legible, with enough quiet detail to reward a final long look.", "closure_rear"),
]


assert len(SPREADS) == 50


def build_prompt(item: dict) -> str:
    return (
        f"meticulously detailed game concept art for Bango-Patoot, original urban-underhive fantasy horror world, "
        f"subject: {item['subject']}, setting: {item['setting']}, visual focus: {item['focus']}, "
        f"palette emphasis: {item['palette']}, highly readable silhouette language, production-ready visual-development illustration, "
        f"cinematic lighting, cohesive material logic, premium artbook quality, no text, no watermark, no logos"
    )


def manifest_output_name(item: dict) -> str:
    return f"{item['index']:02d}_{item['slug']}.png"


def dialogue_for_spread(item: dict) -> list[dict]:
    lines = DIALOGUE_MAP.get(item["slug"], [])
    return [{"speaker": speaker, "text": text} for speaker, text in lines]


def overlays_for_spread(item: dict) -> list[str]:
    base = OVERLAY_MAP.get(item["slug"], [])
    if item["mode"] in {"appendix_glossary", "legal_epilogue", "closure_rear"}:
        return base
    if not base:
        base = [item["section"], item["palette"]]
    return base[:3]


def build_manifest() -> list[dict]:
    manifest = []
    for item in SPREADS:
        manifest.append(
            {
                "name": item["slug"],
                "prompt": build_prompt(item),
                "w": ASSET_SIZE[0],
                "h": ASSET_SIZE[1],
                "out": str((ASSET_DIR / manifest_output_name(item)).relative_to(PACKAGE_DIR)),
                "api_units": UNITS_PER_IMAGE,
                "model": "recraftv4",
                "page_dialogue": dialogue_for_spread(item),
                "page_overlays": overlays_for_spread(item),
            }
        )
    return manifest


def wrap_pixels(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    parts = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            parts.append("")
            continue
        line = words[0]
        for word in words[1:]:
            trial = f"{line} {word}"
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                line = trial
            else:
                parts.append(line)
                line = word
        parts.append(line)
    return "\n".join(parts)


def measure_multiline(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, spacing: int) -> tuple[int, int]:
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def panel(base: Image.Image, box, fill, outline, radius=24, width=2):
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)
    base.alpha_composite(overlay)


def darken(image: Image.Image, factor: float) -> Image.Image:
    return ImageEnhance.Brightness(image).enhance(factor)


def load_asset(item: dict) -> Image.Image:
    path = ASSET_DIR / manifest_output_name(item)
    if not path.exists():
        raise FileNotFoundError(f"Missing generated asset: {path}")
    with Image.open(path) as source:
        image = source.convert("RGBA")
    image = image.resize(PAGE_SIZE, Image.Resampling.LANCZOS)
    image.save(path, format="PNG")
    return image


def draw_page_number(draw: ImageDraw.ImageDraw, page_number: int):
    label = f"{page_number:03d}"
    draw.text((PAGE_SIZE[0] - 88, PAGE_SIZE[1] - 44), label, font=FONT_TINY, fill=(236, 232, 220, 220))


def dialogue_layout(page_number: int, bubble_index: int) -> tuple[int, int, int]:
    anchors = [
        (1190, 110, 330),
        (1040, 620, 360),
        (160, 620, 360),
        (180, 120, 320),
    ]
    return anchors[(page_number + bubble_index) % len(anchors)]


def draw_discrete_overlays(base: Image.Image, overlay_lines: list[str], page_number: int) -> None:
    if not overlay_lines:
        return
    draw = ImageDraw.Draw(base)
    positions = [
        (92, 88),
        (PAGE_SIZE[0] - 360, 92),
        (PAGE_SIZE[0] - 340, PAGE_SIZE[1] - 132),
    ]
    for index, text in enumerate(overlay_lines[:3]):
        x, y = positions[(page_number + index) % len(positions)]
        wrapped = wrap_pixels(draw, text, FONT_TINY, 220)
        width, height = measure_multiline(draw, wrapped, FONT_TINY, 5)
        panel(base, (x - 10, y - 8, x + width + 14, y + height + 12), (10, 12, 16, 118), (255, 244, 220, 34), radius=14, width=1)
        draw.multiline_text((x, y), wrapped, font=FONT_TINY, fill=(232, 228, 220, 198), spacing=5)


def draw_dialogue_bubbles(base: Image.Image, dialogue: list[dict], page_number: int) -> None:
    if not dialogue:
        return
    draw = ImageDraw.Draw(base)
    for bubble_index, line in enumerate(dialogue[:2]):
        x, y, max_width = dialogue_layout(page_number, bubble_index)
        speaker = line["speaker"].upper()
        body = f"{speaker}: {line['text']}"
        wrapped = wrap_pixels(draw, body, FONT_SMALL, max_width - 30)
        width, height = measure_multiline(draw, wrapped, FONT_SMALL, 8)
        box = (x, y, x + width + 32, y + height + 28)
        panel(base, box, (250, 246, 234, 214), (120, 84, 42, 120), radius=22, width=2)
        tail_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        tail = ImageDraw.Draw(tail_overlay)
        if x > PAGE_SIZE[0] // 2:
            tail.polygon([(x + 40, box[3] - 4), (x + 18, box[3] + 24), (x + 76, box[3] - 2)], fill=(250, 246, 234, 214), outline=(120, 84, 42, 120))
        else:
            tail.polygon([(box[2] - 42, box[3] - 4), (box[2] - 18, box[3] + 24), (box[2] - 78, box[3] - 2)], fill=(250, 246, 234, 214), outline=(120, 84, 42, 120))
        base.alpha_composite(tail_overlay)
        draw.multiline_text((x + 16, y + 12), wrapped, font=FONT_SMALL, fill=(40, 28, 22, 255), spacing=8)


def apply_page_overlays(base: Image.Image, item: dict, page_number: int, page_type: str) -> Image.Image:
    dialogue = dialogue_for_spread(item) if page_type in {"cover", "intro", "art", "closure", "rear"} else []
    overlays = overlays_for_spread(item)
    draw_discrete_overlays(base, overlays, page_number)
    draw_dialogue_bubbles(base, dialogue, page_number)
    return base


def standard_text_page(item: dict, page_number: int) -> Image.Image:
    base = darken(load_asset(item).filter(ImageFilter.GaussianBlur(radius=1.5)), 0.46)
    panel(base, (70, 68, 840, 832), (10, 12, 16, 198), (255, 245, 220, 54))
    draw = ImageDraw.Draw(base)
    draw.text((110, 108), item["section"].upper(), font=FONT_SECTION, fill=(245, 196, 118, 255))
    draw.text((110, 150), item["title"], font=FONT_HEADING, fill=(246, 242, 232, 255))
    body = (
        f"World Role\n{item['world_role']}\n\n"
        f"Gameplay Translation\n{item['gameplay_role']}\n\n"
        f"Visual Directive\n{item['visual_directive']}\n\n"
        f"Palette\n{item['palette']}"
    )
    wrapped = wrap_pixels(draw, body, FONT_BODY, 650)
    draw.multiline_text((110, 214), wrapped, font=FONT_BODY, fill=(232, 232, 228, 255), spacing=10)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "text")


def standard_art_page(item: dict, page_number: int) -> Image.Image:
    base = load_asset(item)
    panel(base, (70, 694, 760, 832), (8, 10, 14, 178), (255, 244, 220, 48))
    draw = ImageDraw.Draw(base)
    draw.text((102, 722), item["title"], font=FONT_HEADING, fill=(246, 242, 232, 255))
    wrapped = wrap_pixels(draw, item["focus"], FONT_SMALL, 600)
    draw.multiline_text((102, 770), wrapped, font=FONT_SMALL, fill=(230, 230, 224, 255), spacing=8)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "art")


def cover_page(item: dict, page_number: int) -> Image.Image:
    base = load_asset(item)
    panel(base, (120, 82, 1480, 286), (9, 11, 15, 154), (255, 245, 228, 70), radius=30)
    draw = ImageDraw.Draw(base)
    draw.text((800, 122), TITLE, font=FONT_TITLE, fill=(248, 242, 228, 255), anchor="ma")
    draw.text((800, 208), "Original 3DS World And Entities Concept Artbook", font=FONT_SECTION, fill=(242, 196, 124, 255), anchor="ma")
    return apply_page_overlays(base, item, page_number, "cover")


def toc_page(item: dict, page_number: int) -> Image.Image:
    base = darken(load_asset(item).filter(ImageFilter.GaussianBlur(radius=1.4)), 0.42)
    panel(base, (86, 76, 950, 824), (12, 16, 20, 206), (255, 244, 220, 50))
    draw = ImageDraw.Draw(base)
    draw.text((126, 114), "TABLE OF CONTENTS", font=FONT_HEADING, fill=(246, 242, 232, 255))
    toc_lines = [
        "001  Cover Page",
        "002  Table of Contents",
        "003  Introductory Page",
        "004-094  Design Content Pages",
        "095  Appendix",
        "096  Glossary",
        "097  Legal / Copyright / Publication",
        "098  Epilogue / Closing Summary",
        "099  Final Closure Image",
        "100  Rear Cover",
    ]
    draw.multiline_text((126, 188), "\n".join(toc_lines), font=FONT_BODY, fill=(232, 232, 228, 255), spacing=16)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "toc")


def intro_page(item: dict, page_number: int) -> Image.Image:
    base = darken(load_asset(item).filter(ImageFilter.GaussianBlur(radius=1.0)), 0.54)
    panel(base, (100, 110, 1020, 780), (10, 12, 16, 198), (255, 244, 220, 58))
    draw = ImageDraw.Draw(base)
    draw.text((138, 148), "INTRODUCTORY PAGE", font=FONT_SECTION, fill=(242, 196, 124, 255))
    draw.text((138, 188), item["title"], font=FONT_HEADING, fill=(246, 242, 232, 255))
    intro_text = (
        "Bango-Patoot is a 3D collectathon action-RPG for Nintendo 3DS set inside a vertical city-underworld where shrine ritual, labor history, gang rule, machine religion, and cryptid folklore all overlap. "
        "This artbook package profiles the game's cast, districts, factions, bosses, systems, props, interface, and closing publication matter through one hundred pages assembled from a two-thousand-unit Recraft concept pass.\n\n"
        "The visual direction favors tactile municipal mysticism: comb-metal, patched cloth, wax residue, condemned chapel steel, fungal runoff, and worker-made route signage. "
        "Every entity is designed to reinforce the same central fantasy: Bango and Patoot descending through a wounded but legible city-body that can still be tended, remembered, and reclaimed."
    )
    wrapped = wrap_pixels(draw, intro_text, FONT_BODY, 810)
    draw.multiline_text((138, 258), wrapped, font=FONT_BODY, fill=(232, 232, 228, 255), spacing=12)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "intro")


def appendix_page(item: dict, page_number: int) -> Image.Image:
    base = darken(load_asset(item).filter(ImageFilter.GaussianBlur(radius=1.2)), 0.46)
    panel(base, (84, 84, 980, 818), (12, 14, 18, 210), (255, 244, 220, 54))
    draw = ImageDraw.Draw(base)
    draw.text((124, 118), "APPENDIX", font=FONT_HEADING, fill=(246, 242, 232, 255))
    appendix = (
        "A. District route memory checklist\n"
        "B. Shrine state before/after notes\n"
        "C. Faction silhouette comparison references\n"
        "D. Boss arena landmark hierarchy\n"
        "E. Collectible family shape keys\n"
        "F. 3DS readability and UI contrast rules\n"
        "G. Material swatch shorthand for outsourcing\n"
        "H. Naming rules for wards, rails, shrines, and hymn engines"
    )
    draw.multiline_text((124, 200), appendix, font=FONT_BODY, fill=(232, 232, 228, 255), spacing=16)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "appendix")


def glossary_page(item: dict, page_number: int) -> Image.Image:
    base = darken(load_asset(item).filter(ImageFilter.GaussianBlur(radius=1.2)), 0.44)
    panel(base, (84, 84, 1120, 818), (12, 14, 18, 214), (255, 244, 220, 54))
    draw = ImageDraw.Draw(base)
    draw.text((124, 118), "GLOSSARY", font=FONT_HEADING, fill=(246, 242, 232, 255))
    glossary = (
        "Apiary Junction: central shrine-and-merchant hub of the undercity.\n"
        "EgoSphere: relationship logic tracking trust, fear, debt, respect, rivalry, and mimicry.\n"
        "Hive Sigil: primary progression object used to open districts and restore shrine lattices.\n"
        "Lantern Kin: rescued hive-children whose safety alters shrine warmth and civic tone.\n"
        "Nocturne Note: common currency and codex-linked scrap of undercity memory.\n"
        "Shrine Pollen: catalyst matter used in refinement, upgrades, and ward tuning.\n"
        "Witchcoil: final obedience-engine spire built from city infrastructure and ritual doctrine.\n"
        "Choir Scrap: doctrinal fragment tied to enemy ideology, hidden routes, and codex lore."
    )
    draw.multiline_text((124, 198), glossary, font=FONT_BODY, fill=(232, 232, 228, 255), spacing=16)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "glossary")


def legal_page(item: dict, page_number: int) -> Image.Image:
    base = darken(load_asset(item).filter(ImageFilter.GaussianBlur(radius=1.0)), 0.48)
    panel(base, (110, 110, 1160, 790), (18, 14, 12, 214), (255, 226, 196, 58))
    draw = ImageDraw.Draw(base)
    draw.text((150, 144), "LEGAL / COPYRIGHT / PUBLICATION", font=FONT_HEADING, fill=(246, 236, 220, 255))
    text = (
        "Bango-Patoot is an original drIpTECH property presented here as a development concept art package. All names, environments, factions, visual motifs, and fictional institutions described in this volume belong to the same original project world.\n\n"
        "This publication compiles generated concept imagery, design writing, and formatting intended for internal creative development, pitch support, and production planning. It is not a retail software build, legal filing, or public license grant.\n\n"
        "All image outputs in this package were generated into user-owned local project storage through the project's Recraft pipeline and then assembled into ECBMPS format for internal review."
    )
    wrapped = wrap_pixels(draw, text, FONT_SMALL, 940)
    draw.multiline_text((150, 232), wrapped, font=FONT_SMALL, fill=(238, 229, 215, 255), spacing=12)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "legal")


def epilogue_page(item: dict, page_number: int) -> Image.Image:
    base = darken(load_asset(item).filter(ImageFilter.GaussianBlur(radius=0.8)), 0.5)
    panel(base, (140, 160, 1120, 742), (10, 12, 16, 188), (255, 244, 220, 52))
    draw = ImageDraw.Draw(base)
    draw.text((180, 198), "EPILOGUE / CLOSING SUMMARY", font=FONT_HEADING, fill=(246, 242, 232, 255))
    text = (
        "Bango-Patoot closes not on total restoration but on civic legibility. The city survives, scarred and still politically unstable, yet finally readable as a place that can be tended rather than merely endured.\n\n"
        "The concept package's goal is to give every later asset pass a coherent material language, faction grammar, boss silhouette logic, and district-level emotional cadence. The world should feel authored from service culture, ritual labor, and undercity folklore outward."
    )
    wrapped = wrap_pixels(draw, text, FONT_BODY, 900)
    draw.multiline_text((180, 284), wrapped, font=FONT_BODY, fill=(232, 232, 228, 255), spacing=12)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "epilogue")


def closure_image_page(item: dict, page_number: int) -> Image.Image:
    base = load_asset(item)
    panel(base, (72, 700, 820, 832), (8, 10, 14, 164), (255, 244, 220, 46))
    draw = ImageDraw.Draw(base)
    draw.text((106, 726), "FINAL CLOSURE IMAGE", font=FONT_HEADING, fill=(246, 242, 232, 255))
    draw.multiline_text((106, 772), "A dawn-lit city still wounded, but no longer unreadable.", font=FONT_SMALL, fill=(232, 232, 228, 255), spacing=8)
    draw_page_number(draw, page_number)
    return apply_page_overlays(base, item, page_number, "closure")


def rear_cover_page(item: dict, page_number: int) -> Image.Image:
    base = load_asset(item)
    panel(base, (1000, 88, 1490, 304), (8, 10, 14, 156), (255, 244, 220, 42))
    draw = ImageDraw.Draw(base)
    blurb = (
        "A visual dossier of districts, factions, shrines, cryptids, and civic rituals from the world of Bango-Patoot."
    )
    wrapped = wrap_pixels(draw, blurb, FONT_SMALL, 430)
    draw.multiline_text((1036, 132), wrapped, font=FONT_SMALL, fill=(240, 236, 228, 255), spacing=8)
    return apply_page_overlays(base, item, page_number, "rear")


def build_page_plan() -> list[dict]:
    plan = [
        {"page": 1, "type": "cover", "spread": 1},
        {"page": 2, "type": "toc", "spread": 1},
        {"page": 3, "type": "intro", "spread": 2},
        {"page": 4, "type": "art", "spread": 2},
    ]
    for spread_index in range(3, 48):
        plan.append({"page": len(plan) + 1, "type": "text", "spread": spread_index})
        plan.append({"page": len(plan) + 1, "type": "art", "spread": spread_index})
    plan.append({"page": 95, "type": "appendix", "spread": 48})
    plan.append({"page": 96, "type": "glossary", "spread": 48})
    plan.append({"page": 97, "type": "legal", "spread": 49})
    plan.append({"page": 98, "type": "epilogue", "spread": 49})
    plan.append({"page": 99, "type": "closure", "spread": 50})
    plan.append({"page": 100, "type": "rear", "spread": 50})
    for entry in plan:
        item = SPREADS[entry["spread"] - 1]
        entry["dialogue"] = dialogue_for_spread(item)
        entry["overlays"] = overlays_for_spread(item)
    assert len(plan) == 100
    return plan


def render_page(page_spec: dict) -> Image.Image:
    item = SPREADS[page_spec["spread"] - 1]
    page_type = page_spec["type"]
    page_number = page_spec["page"]
    if page_type == "cover":
        return cover_page(item, page_number)
    if page_type == "toc":
        return toc_page(item, page_number)
    if page_type == "intro":
        return intro_page(item, page_number)
    if page_type == "text":
        return standard_text_page(item, page_number)
    if page_type == "art":
        return standard_art_page(item, page_number)
    if page_type == "appendix":
        return appendix_page(item, page_number)
    if page_type == "glossary":
        return glossary_page(item, page_number)
    if page_type == "legal":
        return legal_page(item, page_number)
    if page_type == "epilogue":
        return epilogue_page(item, page_number)
    if page_type == "closure":
        return closure_image_page(item, page_number)
    if page_type == "rear":
        return rear_cover_page(item, page_number)
    raise ValueError(f"Unsupported page type: {page_type}")


def write_profile_files() -> None:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {TITLE} World And Entities Design Profile",
        "",
        "## Purpose",
        "This document is the detailed world-and-entities profile for the original Nintendo 3DS project Bango-Patoot. It is paired with a 50-image, 2000-unit Recraft concept pass and the 100-page concept artbook assembled from that pass.",
        "",
        "## Visual Foundation",
        "- World identity: industrial shrine-fantasy undercity horror with civic memory, worker ritual, cable transport, fungal runoff, and machine-lit devotion.",
        "- Character identity: tactile, asymmetrical, practical silhouettes designed for 3DS readability and strong duo interplay.",
        "- Material identity: comb-metal, patched cloth, wax residue, damp brick, brass patina, rail grease, archive paper, and shrine ceramics.",
        "- Lighting identity: warm communal lanterns versus coercive broadcast light, always with district-specific logic.",
        "",
        "## Spread Profiles",
        "",
    ]
    for item in SPREADS:
        lines.extend(
            [
                f"### {item['index']:02d}. {item['title']}",
                f"- Section: {item['section']}",
                f"- Subject: {item['subject']}",
                f"- Setting: {item['setting']}",
                f"- Visual Focus: {item['focus']}",
                f"- Palette: {item['palette']}",
                f"- World Role: {item['world_role']}",
                f"- Gameplay Translation: {item['gameplay_role']}",
                f"- Visual Directive: {item['visual_directive']}",
                f"- Dialogue Bubble Copy: {' | '.join(f'{line['speaker']}: {line['text']}' for line in dialogue_for_spread(item)) if dialogue_for_spread(item) else 'None'}",
                f"- Descriptive Overlay Copy: {' | '.join(overlays_for_spread(item)) if overlays_for_spread(item) else 'None'}",
                "",
            ]
        )
    glossary = textwrap.dedent(
        """
        ## Glossary Snapshot
        - Apiary Junction: central shrine-and-service hub.
        - Hive Sigil: primary macro progression object.
        - Nocturne Note: common currency and codex scrap.
        - Lantern Kin: rescued hive-children who alter social and shrine states.
        - Shrine Pollen: catalyst material for refinement and growth.
        - EgoSphere: NPE relationship logic shaping prices, rumor access, warning behaviors, and social-state drift.
        - Witchcoil: the final obedience-engine spire built from ritual and infrastructure.
        """
    ).strip()
    lines.extend([glossary, ""])
    PROFILE_MD.write_text("\n".join(lines), encoding="utf-8")
    PROFILE_TXT.write_text("\n".join(lines), encoding="utf-8")


def write_manifest_and_plan() -> None:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    PAGE_PLAN_PATH.write_text(json.dumps(build_page_plan(), indent=2), encoding="utf-8")


def render_pages() -> None:
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    for page_spec in build_page_plan():
        image = render_page(page_spec)
        out_path = PAGE_DIR / f"page{page_spec['page']:03d}.png"
        image.save(out_path, format="PNG")
        print(f"Saved {out_path}")


def compile_book(compiler_path: Path | None = None) -> None:
    if compiler_path is None:
        compiler_path = ROOT.parent / "ecbmps_ccp_studio" / "build" / "ecbmps_compiler.exe"
    if not compiler_path.exists():
        raise FileNotFoundError(f"Missing ECBMPS compiler: {compiler_path}")
    pages = sorted(PAGE_DIR.glob("page*.png"))
    if len(pages) != 100:
        raise RuntimeError(f"Expected 100 page PNGs, found {len(pages)}")
    command = [str(compiler_path), "-o", str(OUTPUT_BOOK), "-t", TITLE, "-a", AUTHOR] + [str(page) for page in pages]
    subprocess.run(command, check=True)
    print(f"Compiled {OUTPUT_BOOK}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Bango-Patoot concept art package.")
    parser.add_argument("--prepare", action="store_true", help="Write the design profile, 2000-unit Recraft manifest, and page plan.")
    parser.add_argument("--render-pages", action="store_true", help="Render the 100-page PNG artbook from generated assets.")
    parser.add_argument("--compile", action="store_true", help="Compile the rendered pages into an ECBMPS file.")
    parser.add_argument("--compiler", type=Path, help="Override path to ecbmps_compiler.exe.")
    args = parser.parse_args()

    if not (args.prepare or args.render_pages or args.compile):
        parser.error("Select at least one action: --prepare, --render-pages, or --compile")

    if args.prepare:
        write_profile_files()
        write_manifest_and_plan()
        total_units = len(SPREADS) * UNITS_PER_IMAGE
        print(f"Prepared profile and manifest at {PACKAGE_DIR} ({len(SPREADS)} images / {total_units} units).")
    if args.render_pages:
        render_pages()
    if args.compile:
        compile_book(args.compiler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())