from __future__ import annotations

import json
import math
import textwrap
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
GENERATED_DIR = ROOT / "generated"
README_PATH = ROOT / "README.md"
GAME_BIBLE_PATH = DOCS_DIR / "KIN_DARK_GAME_BIBLE.md"
RUNTIME_SPEC_PATH = DOCS_DIR / "KIN_DARK_RUNTIME_AND_CONTROLLER_SPEC.md"
ASSET_OVERVIEW_PATH = DOCS_DIR / "KIN_DARK_ASSET_PROGRAM_OVERVIEW.md"
TUTORIAL_SLICE_PATH = DOCS_DIR / "KIN_DARK_TUTORIAL_SLICE.md"
MASTER_BOOK_PATH = GENERATED_DIR / "kin_dark_master_book.md"
STORY_SUMMARY_PATH = GENERATED_DIR / "kin_dark_story_summary.json"
TUTORIAL_SUMMARY_PATH = GENERATED_DIR / "kin_dark_tutorial_slice.json"
GRAPHICS_MANIFEST_PATH = GENERATED_DIR / "kin_dark_graphics_manifest.jsonl"
GRAPHICS_SUMMARY_PATH = GENERATED_DIR / "kin_dark_graphics_summary.json"
AUDIO_MANIFEST_PATH = GENERATED_DIR / "kin_dark_audio_manifest.jsonl"
ASSET_SUMMARY_PATH = GENERATED_DIR / "kin_dark_asset_summary.json"
GAME_PROJECT_PATH = GENERATED_DIR / "kin_dark_game_project.json"
DRIP3D_PROJECT_PATH = GENERATED_DIR / "kin_dark_game_project.drip3d.json"


GRAPHICS_TARGET = 109_867
AUDIO_TARGET = 2_037
SONG_TARGET = 200
DIRECTIONS = ["north", "north_east", "east", "south_east", "south", "south_west", "west", "north_west"]
MESH_ANGLES = ["front", "front_right", "right", "rear_right", "rear", "front_left"]


@dataclass(frozen=True)
class Protagonist:
    slug: str
    name: str
    role: str
    look: str
    combat_profile: str
    traversal_profile: str
    timeline_premise: str
    animation_set: tuple[str, ...]
    signature_tools: tuple[str, ...]


@dataclass(frozen=True)
class PlotArc:
    index: int
    title: str
    hours: int
    focus: str
    district: str
    premise: str
    collision: str
    outcome: str


PROTAGONISTS = (
    Protagonist(
        slug="moe",
        name="Moe",
        role="recently divorced vacuum cleaner salesman turned pistol-and-flashlight survivor",
        look="solemn, balding, stubbled, wearing a stained ribbed undershirt, scraggly cut-off shorts, and brown loafers",
        combat_profile="light sidearm gunplay, flashlight cone management, desperate close-range scrapping, and recoil-heavy finishers",
        traversal_profile="door breaching, ledge vaulting, flashlight tracing, shove interactions, and grounded urban scrambling",
        timeline_premise="Moe starts in the low-rent apartment belt and follows the mythicozoocryptid outbreak through debt collectors, failed marriages, ruined retail blocks, and institutional cover-ups.",
        animation_set=(
            "idle",
            "walk",
            "run",
            "aim_reticle",
            "flashlight_scan",
            "quickdraw",
            "pistol_fire",
            "reload",
            "dodge_roll",
            "vault",
            "inspect",
            "hold_interact",
        ),
        signature_tools=("vacuum-salesman sample case", "flashlight", "pistol", "receipt ledger"),
    ),
    Protagonist(
        slug="yil",
        name="Yil",
        role="gnome mechanic-magician who can rewrite broken infrastructure with ritual engineering",
        look="small and sharp-eyed, dressed in a lavish robe, tri-cornered hat, broad mustache, curled leather boots, and a black belt with a spiral buckle",
        combat_profile="rune-charged casts, turret sigils, reality hinge repairs, area denial glyphs, and burst-navigation spells",
        traversal_profile="blink stepping, levitation rails, rune climbing, machinery bridging, and magical short-range glide control",
        timeline_premise="Yil enters from the sewer workshops and abandoned machine sanctums, tracking why the city’s utility grid is acting like a summoning lattice.",
        animation_set=(
            "idle",
            "walk",
            "run",
            "aim_spell",
            "wrench_cast",
            "sigil_burst",
            "ward_raise",
            "blink_step",
            "glide_rune",
            "mechanic_climb",
            "inspect",
            "hold_interact",
        ),
        signature_tools=("spiral wrench", "glyph satchel", "lantern capacitor", "tricorn relay pins"),
    ),
    Protagonist(
        slug="lou",
        name="Lou",
        role="private investigator monkey who avoids direct combat and puppets threats through telepathic control",
        look="wiry and observant, wearing a trench coat, sneakers, and a detective’s shoulder holster full of notebooks and signal tags",
        combat_profile="telepathic domination, enemy hijack chains, crowd steering, stealth disruption, and evidence-tagging misdirection",
        traversal_profile="all-surface climbing, vent slipping, pipe swinging, perch hopping, and remote interaction through mind-thread focus",
        timeline_premise="Lou begins on the rooftops and transit signage, tracing who benefits from the panic while literally reading intent off the city’s frightened population.",
        animation_set=(
            "idle",
            "walk",
            "run",
            "aim_focus",
            "telepathic_mark",
            "mind_puppet",
            "command_release",
            "wall_climb",
            "ceiling_traverse",
            "perch_leap",
            "inspect",
            "hold_interact",
        ),
        signature_tools=("telepathic lens", "detective notebook", "signal tags", "grapnel cord"),
    ),
)


DISTRICTS = (
    ("vacancy_row", "Vacancy Row", "boarded rental towers, divorce courts, pawn stores, radiator alleys"),
    ("floodcourt_mile", "Floodcourt Mile", "rain-choked boulevards, submerged crosswalks, courthouse drains"),
    ("tin_saint_market", "Tin Saint Market", "collapsed shopping arcades, shrine kiosks, neon awnings"),
    ("rookery_switch", "Rookery Switch", "elevated train wrecks, bird-haunted signal gantries, soot balconies"),
    ("candlelung_towers", "Candlelung Towers", "art deco residential stacks, dangling bridges, blackouts"),
    ("siltglass_sewers", "Siltglass Sewers", "runoff tunnels, ritual pumps, fungal sluices"),
    ("mothline_works", "Mothline Works", "abandoned textile automation lines, belt systems, lint storms"),
    ("choirburn_foundry", "Choirburn Foundry", "steel halls, slag altars, derailed loaders, boiler cathedrals"),
    ("pilgrim_underpass", "Pilgrim Underpass", "pilgrim camps, reliquary traffic, graffiti chapels"),
    ("spite_marina", "Spite Marina", "dry docks, buckled marinas, salt-drenched motels"),
    ("split_reliquary", "Split Reliquary", "museum vaults, broken exhibits, saint-tech archives"),
    ("ninth_station", "Ninth Station", "final transit ring, cracked observatory roof, reality-fissure core"),
)


INSTITUTIONS = (
    "Municipal Fold Office",
    "Night Warranty Syndicate",
    "Bureau of Drainage and Apparitions",
    "Ruin Appraisal Board",
    "Last Family Court",
    "Transit Choir Reserve",
    "Civic Salvage Temperance League",
    "Null Animal Containment Corps",
    "The Red Ledger Newsroom",
    "Bright Mercy Pawn Chain",
    "Voltage Chapel Custodians",
    "The Vacancy Mutual",
)


BOSSES = (
    "The Receipts Bride",
    "Switchyard Gorgon",
    "The Choirburn Foreman",
    "Auntie Sumpglass",
    "The Floodcourt Collector",
    "Motel Saint Ragpicker",
    "The Velvet Ratifier",
    "Maw of Platform Nine",
    "Soot Lung Nickelback",
    "The Spiral Dowser",
    "Dockside Judge Marmoset",
    "The Neon Dog Census",
    "Tallow Ferryman",
    "Rookery Magistrate",
    "The Last Demonstrator",
    "Relay Widow Harlequin",
    "The Debtor Crocodile",
    "Shiverpaste Conductor",
    "The Felt Apostate",
    "Saint Vacancy Prime",
    "The Sewer Parliament",
    "Mother Photoflash",
    "The Locksmith of Teeth",
    "King Cracked Halo",
)


NOTABLE_NPCS = (
    "Vera Coil, motel clerk and rumor broker",
    "Pintle Rusk, subway bell mechanic",
    "Mother Brine, sewer chapel keeper",
    "Detective Cal Latch, Lou's ex-partner",
    "Rollo Pemm, failed landlord and amateur cryptid evangelist",
    "Ness Wire, relay-child map seller",
    "Marya Dint, floodwall paramedic",
    "Hexa Vale, foundry union archivist",
    "Tuppence Woe, roaming court stenographer",
    "Jasper Knurl, blackout florist",
    "Sella Bracket, transit conductor who never leaves Ninth Station",
    "Junebug Pike, spite-marina diver",
    "Crozier Dell, appetites reporter for The Red Ledger",
    "Mimsy Warden, pawn chain regional manager",
    "Basil Knots, divorce mediator turned survival merchant",
    "Olin Muck, underpass clown-evangelist",
    "Penny Rake, flashlight refurbisher",
    "Clover Vane, itinerant cryptid biologist",
    "Doro Pitch, public utility saboteur",
    "Iris Rack, train-yard harmonics singer",
    "Mote Wasp, soot balcony fence-runner",
    "Sister Clack, null-containment field medic",
    "Lem Grist, foundry crane operator",
    "Ria Tens, market stall cartographer",
)


ENEMY_SPECIES = (
    "Stamplick Hounds: receipt-paper canids that track debt, not scent.",
    "Umbra Cranes: skeletal industrial birds that nest in lifted scaffolds.",
    "Radiator Cherubs: steam-bloated hallway imps that scream through vents.",
    "Ticket Leeches: rail-thin parasites that staple themselves to fare gates.",
    "Sump Gloamers: blind eel-mollusk hybrids that pulse at pipe pressure changes.",
    "Halo Vermin: halo-ringed rats bred by reality fissures and billboard light.",
    "Glassback Croakers: frogish sewer prophets with mirrored spines.",
    "Latch Monkeys: lock-picking gutter apes that mob in laughing packs.",
    "Invoice Beetles: lacquered roaches that digest archive dust and glue.",
    "Bell Wives: bridal mantis-things that assemble from drapery and rebar.",
    "Floodcourt Colts: wet horse-jackals that gallop through courthouse water tables.",
    "Tin Saints: counterfeit saint-statues animated by civic panic.",
)


MAJOR_ITEMS = (
    "Moe: flashlight cartridges, panic syringes, vacuum sample tubes, jury-rigged pistol parts",
    "Yil: rune spanners, capacitor charms, bridge sigils, ward coils",
    "Lou: telepathic tags, evidence twine, rumor lenses, rooftop scent markers",
    "Shared: relic debts, ruin keys, transit seals, cryptid marrow tonics, fuse saints, lockout maps",
)


TWEENKIN_PRIMER = {
    "label": "TweenKin",
    "classification": "a fast-adapting invading morph-brood that rides civic stress fractures into Dark",
    "traits": [
        "They hatch where panic, debt, and weak infrastructure stack long enough to make the city feel unfinished.",
        "They are younger, quicker, and more contagious than the older mythicozoocryptids; they imitate public signage, utility noise, and social behavior before they commit to a body.",
        "They travel in clusters that mix scout forms, shrieker forms, latch forms, and larger adulting hulks that borrow features from whatever district they first invade.",
        "They are not the whole problem, but they are the tutorial-era face of the invasion because they attack in ways each protagonist can teach against immediately.",
    ],
    "gameplayTruths": [
        "Moe can stagger TweenKin scouts with flashlight focus and finish them with disciplined sidearm bursts.",
        "Yil can collapse their approach lanes with wards, bridge around their swarms, and overload their nest machinery.",
        "Lou can mark a brood leader, puppet a lesser TweenKin, and turn the pack's coordination against itself.",
        "TweenKin teach the player to read telegraphs, control space, preserve stamina, and exploit each character's specialty instead of mashing through encounters.",
    ],
}


TUTORIAL_SLICE_BEATS = (
    {
        "id": "vacancy_row_cold_open",
        "title": "Vacancy Row Cold Open",
        "district": "Vacancy Row",
        "focusCharacter": "Moe",
        "purpose": "Teach basic locomotion, camera behavior, interaction rules, and emergency pistol rhythm while Dark is still comprehensible.",
        "narrative": "Moe exits a condemned rental block carrying his sample case just as the first TweenKin scouts slip out of split radiator housings and start copying tenant voices.",
        "lessons": [
            "Move with the left stick through hallways, stairwells, alleys, and broken lobby furniture.",
            "Use the right stick to bias the camera and reticle while keeping the body committed to a route.",
            "Hold A for one second on doors, ledges, evidence piles, and civic devices to prove the adaptive context action rule.",
            "Use LT focus to tighten the field of view and expose weak points on frightened TweenKin scouts.",
            "Fire with RT in short bursts, then dodge or vault instead of standing still after recoil.",
        ],
        "encounter": "Three radiator-born TweenKin scouts, one latchling on a fuse box, one panicked civilian, and one blocked fire door.",
        "completionGate": "Moe rescues the civilian, opens the blocked route, and reaches the alley overlook where Dark first becomes visible.",
    },
    {
        "id": "siltglass_service_rites",
        "title": "Siltglass Service Rites",
        "district": "Siltglass Sewers",
        "focusCharacter": "Yil",
        "purpose": "Teach magic traversal, infrastructure interaction, spatial denial, and route creation.",
        "narrative": "Yil interrupts a drain-hall maintenance prayer and finds TweenKin crawling through unfinished ritual repairs like feral current.",
        "lessons": [
            "Chain walk, run, blink, and glide movement to cross gaps Moe could never take alone.",
            "Use RT casts and X/Y/B actions to place wards, burst sigils, and temporary bridge logic.",
            "Use LB/RB as spell modifiers to swap between movement-safe repair and aggressive denial patterns.",
            "Aim utility casts with the same right-stick reticle language learned from Moe so the control scheme stays unified.",
            "Repairing the city is itself a mechanic: every fixed conduit opens space, redirects enemies, or teaches that Dark is a combat puzzle.",
        ],
        "encounter": "TweenKin nestlings inside pump housings, a flooded conduit lane, and a broken levitation rail that must be reactivated under pressure.",
        "completionGate": "Yil energizes the rail bridge and seals the first public breach map node for the shared timeline.",
    },
    {
        "id": "rookery_signal_test",
        "title": "Rookery Signal Test",
        "district": "Rookery Switch",
        "focusCharacter": "Lou",
        "purpose": "Teach stealth, wall traversal, remote interaction, evidence marking, and controlled enemy hijack.",
        "narrative": "Lou tracks a pirate panic broadcast into the train gantries and discovers the TweenKin are learning people by listening to them scream.",
        "lessons": [
            "Traverse walls, pipes, and ceilings with Lou to teach vertical route reading.",
            "Use LT and the reticle to scan evidence points, speakers, vents, and target minds without entering open combat.",
            "Use Lou's action set to mark, puppet, and release a TweenKin instead of killing every threat directly.",
            "Learn that some encounters are solved by redirection, distraction, and social rescue rather than brute damage.",
            "Use the map overlay on View to read district connectivity, vents, rooftop shortcuts, and timeline contamination markers.",
        ],
        "encounter": "A signal tower full of shrieker TweenKin, one hijackable scout, a trapped archivist, and a loudspeaker array feeding the brood.",
        "completionGate": "Lou saves the archivist and tags the first confirmed source of TweenKin coordination for all timelines.",
    },
    {
        "id": "dark_city_panorama",
        "title": "Dark City Panorama",
        "district": "Floodcourt Mile",
        "focusCharacter": "All",
        "purpose": "Introduce Dark as a connected city-state and teach timeline switching as a strategic layer rather than a menu abstraction.",
        "narrative": "The three protagonists independently reach floodlit overlooks that line up into one shared panorama: courthouses leaking records, towers blacking out, market saints twitching awake, and Ninth Station pulsing at the horizon.",
        "lessons": [
            "Dark is one contiguous map, not disconnected stages.",
            "Districts have identities, institutions, traversal languages, and threat flavors that persist across protagonists.",
            "Timeline progress is shared: opening a gate, killing a nest, or stabilizing a route affects everyone.",
            "View opens the city map, contamination spread, and tutorial recap cards so the player can orient without leaving fiction.",
        ],
        "encounter": "A non-combat city reveal with optional inspection nodes, threat callouts, and district flavor barks.",
        "completionGate": "The player understands where Vacancy Row, Floodcourt Mile, Tin Saint Market, Rookery Switch, and Ninth Station sit relative to each other.",
    },
    {
        "id": "three_lane_convergence",
        "title": "Three-Lane Convergence",
        "district": "Tin Saint Market",
        "focusCharacter": "All",
        "purpose": "Combine every lesson into one orchestrated multi-character survival encounter against the TweenKin advance.",
        "narrative": "A false-saint procession collapses into a live TweenKin bloom in the market arcade, forcing Moe, Yil, and Lou to stabilize the same disaster through different means.",
        "lessons": [
            "Moe handles direct rescue and frontal suppression.",
            "Yil controls the battlefield by repairing or sabotaging market machinery in real time.",
            "Lou reads civilian flow, hijacks flankers, and prevents panic feedback from maturing the brood.",
            "Combat, traversal, interaction, evidence, and soft-lock aiming all share one control logic even when the verbs change.",
            "The player leaves the tutorial knowing each character is incomplete alone but devastating in sequence.",
        ],
        "encounter": "TweenKin scouts, shriekers, latch forms, one proto-hulk, civilians to rescue, machinery to stabilize, and a market gate to reopen.",
        "completionGate": "The city grants access to free-roam routes and the first major arc, with the TweenKin invasion now fully legible as the immediate threat layer.",
    },
)


def build_tutorial_slice() -> dict[str, object]:
    protagonist_lenses = []
    for hero in PROTAGONISTS:
        protagonist_lenses.append(
            {
                "id": hero.slug,
                "name": hero.name,
                "role": hero.role,
                "combatFocus": hero.combat_profile,
                "traversalFocus": hero.traversal_profile,
                "signatureTools": list(hero.signature_tools),
                "lessons": {
                    "movement": {
                        "moe": [
                            "read grounded routes quickly",
                            "vault and shove through cluttered interiors",
                            "keep movement readable while aiming under pressure",
                        ],
                        "yil": [
                            "blink across broken space",
                            "glide and rail between repair nodes",
                            "treat traversal powers as route-building tools",
                        ],
                        "lou": [
                            "read vertical spaces as valid paths",
                            "traverse walls, vents, and pipes without losing aim context",
                            "treat stealth and positioning as mobility",
                        ],
                    }[hero.slug],
                    "combat": {
                        "moe": [
                            "focus with LT before firing",
                            "use RT bursts, not panic dumping",
                            "dodge after recoil and rescue civilians during fights",
                        ],
                        "yil": [
                            "use stance modifiers to retune spells",
                            "seal lanes with wards before damaging targets",
                            "repair and destroy infrastructure as offensive choices",
                        ],
                        "lou": [
                            "mark targets before committing",
                            "redirect enemies instead of always finishing them",
                            "preserve social space while dismantling a threat network",
                        ],
                    }[hero.slug],
                },
            }
        )

    control_language = {
        "movement": {
            "leftStick": "omnidirectional locomotion through Dark's interiors, rooftops, ladders, and flood lanes",
            "rightStick": "shared reticle-and-camera grammar across every protagonist",
            "LT": "focus, zoom, soft lock, scan, or precision intent depending on the protagonist and context",
        },
        "combat": {
            "RT": "primary attack or active discharge",
            "LB": "left modifier for stance, spell, telepathic, or traversal variation",
            "RB": "right modifier for alternate stance, power routing, or support action",
            "X": "utility combat action",
            "Y": "mobility-special or power-special action",
            "B": "defensive, evasive, or release action",
        },
        "basics": {
            "A": "adaptive context action; hold for one second to commit to interact, rescue, inspect, repair, or open",
            "View": "map, investigation overlays, timeline recap, city index, and tutorial reminder layer",
            "Menu": "pause, inventory, accessibility, quest log, and clean quit",
        },
    }

    city_intro = {
        "cityName": "Dark",
        "premise": "Dark is a contiguous civic nightmare where debt, maintenance neglect, shame, faith, commerce, and transit all physically mutate under pressure.",
        "districtPrimer": [
            {
                "district": title,
                "id": slug,
                "whatPlayerLearns": {
                    "vacancy_row": "how domestic collapse becomes the first battlefield",
                    "floodcourt_mile": "how law, records, and drainage turn into navigable horror",
                    "tin_saint_market": "how crowds, saints, and salvage become a multi-character systems fight",
                    "rookery_switch": "how vertical transit ruins reshape movement and stealth",
                    "candlelung_towers": "how survival politics turn housing into a siege",
                    "siltglass_sewers": "how the city underneath the city governs what breaks above",
                    "mothline_works": "how dead industry still wants labor",
                    "choirburn_foundry": "how machinery and liturgy combine into weaponized production",
                    "pilgrim_underpass": "how uneasy coexistence differs from control",
                    "spite_marina": "how the coast widens the outbreak",
                    "split_reliquary": "how Dark remembers previous collapses",
                    "ninth_station": "where all routes converge and the city reveals what it has hidden",
                }[slug],
                "direction": direction,
            }
            for slug, title, direction in DISTRICTS
        ],
    }

    return {
        "sliceName": "Dark Arrival / TweenKin First Breach",
        "intent": "First-play onboarding that teaches the unified control language, all three protagonists, baseline mechanics, Dark's district logic, and the immediate threat of the invading TweenKin.",
        "playtimeMinutes": 45,
        "newGameRule": "fresh boot enters this slice before unrestricted city progression",
        "tweenkinPrimer": TWEENKIN_PRIMER,
        "controlLanguage": control_language,
        "protagonistLenses": protagonist_lenses,
        "cityIntroduction": city_intro,
        "beats": list(TUTORIAL_SLICE_BEATS),
        "exitState": {
            "districtsUnlocked": ["vacancy_row", "floodcourt_mile", "tin_saint_market", "rookery_switch", "siltglass_sewers"],
            "sharedSystemsUnlocked": [
                "timeline_state_map",
                "district_fast_orientation",
                "evidence_tracking",
                "basic_supply_management",
                "tweenkin_bestiary_entry",
            ],
            "playerExpectation": "The player should understand how to move, fight, inspect, traverse, rescue, and switch mental models between Moe, Yil, and Lou while reading Dark as one shared city under active invasion.",
        },
    }


def render_tutorial_slice_markdown(tutorial: dict[str, object]) -> str:
    primer_lines = [f"- {line}" for line in tutorial["tweenkinPrimer"]["traits"]]
    gameplay_lines = [f"- {line}" for line in tutorial["tweenkinPrimer"]["gameplayTruths"]]
    primer_block = textwrap.indent("\n".join(primer_lines), "        ")
    gameplay_block = textwrap.indent("\n".join(gameplay_lines), "        ")

    control_sections = []
    for group, mapping in tutorial["controlLanguage"].items():
        lines = [f"- {button}: {description}" for button, description in mapping.items()]
        control_sections.append(f"### {group.replace('_', ' ').title()}\n\n" + "\n".join(lines))
    control_block = textwrap.indent("\n\n".join(control_sections), "        ")

    protagonist_sections = []
    for protagonist in tutorial["protagonistLenses"]:
        movement_lines = "\n".join(f"- {item}" for item in protagonist["lessons"]["movement"])
        combat_lines = "\n".join(f"- {item}" for item in protagonist["lessons"]["combat"])
        protagonist_sections.append(
            "\n".join(
                [
                    f"### {protagonist['name']}",
                    "",
                    f"- Role: {protagonist['role']}",
                    f"- Combat focus: {protagonist['combatFocus']}",
                    f"- Traversal focus: {protagonist['traversalFocus']}",
                    f"- Signature tools: {', '.join(protagonist['signatureTools'])}",
                    "",
                    "Movement tutorial points:",
                    movement_lines,
                    "",
                    "Combat tutorial points:",
                    combat_lines,
                ]
            )
        )
    protagonist_block = textwrap.indent("\n\n".join(protagonist_sections), "        ")

    district_lines = [
        f"- {entry['district']}: {entry['whatPlayerLearns']} ({entry['direction']})"
        for entry in tutorial["cityIntroduction"]["districtPrimer"]
    ]
    district_block = textwrap.indent("\n".join(district_lines), "        ")

    beat_sections = []
    for beat in tutorial["beats"]:
        lesson_lines = "\n".join(f"- {lesson}" for lesson in beat["lessons"])
        beat_sections.append(
            "\n".join(
                [
                    f"### {beat['title']}",
                    "",
                    f"- Focus: {beat['focusCharacter']}",
                    f"- District: {beat['district']}",
                    f"- Purpose: {beat['purpose']}",
                    f"- Narrative beat: {beat['narrative']}",
                    f"- Encounter payload: {beat['encounter']}",
                    f"- Completion gate: {beat['completionGate']}",
                    "",
                    "Lesson delivery:",
                    lesson_lines,
                ]
            )
        )
    beat_block = textwrap.indent("\n\n".join(beat_sections), "        ")

    unlocked_lines = [f"- {item}" for item in tutorial["exitState"]["sharedSystemsUnlocked"]]
    unlocked_block = textwrap.indent("\n".join(unlocked_lines), "        ")

    return normalize_markdown(
        textwrap.dedent(
            f"""
        # Kin Dark Tutorial Slice

        ## Intent

        - Slice name: {tutorial['sliceName']}
        - Goal: {tutorial['intent']}
        - Expected runtime: {tutorial['playtimeMinutes']} minutes
        - Boot rule: {tutorial['newGameRule']}

        ## TweenKin Primer

        - Classification: {tutorial['tweenkinPrimer']['classification']}

    {primer_block}

        ## Gameplay Truths About TweenKin

    {gameplay_block}

        ## Unified Control Language

    {control_block}

        ## Protagonist Teaching Roles

    {protagonist_block}

        ## Introducing Dark

        - {tutorial['cityIntroduction']['premise']}

    {district_block}

        ## Tutorial Beat Flow

    {beat_block}

        ## Exit State

        - Districts unlocked after the slice: {', '.join(tutorial['exitState']['districtsUnlocked'])}
        - Shared systems unlocked:

    {unlocked_block}

        - Expected player understanding: {tutorial['exitState']['playerExpectation']}
        """
        )
    )


PLOT_ARCS = (
    PlotArc(1, "Vacancy Notices", 18, "Moe", "Vacancy Row", "The city starts with evictions, unpaid debts, and the first cryptids slipping through leaking apartment walls.", "Moe mistakes the outbreak for a neighborhood scam until a mythic intruder takes one of his sales routes apart from the inside.", "Moe survives long enough to decide the city is lying about what is happening."),
    PlotArc(2, "Wet Law", 20, "Moe", "Floodcourt Mile", "Courthouse runoff, divorce archives, and drowned clerks turn legal paperwork into a monster habitat.", "Moe chases proof of his ex-wife's disappearance and discovers the court feeds disappearances into a municipal secrecy machine.", "The player learns the outbreak follows institutional shame as much as literal cracks."),
    PlotArc(3, "Wrench Gospel", 22, "Yil", "Siltglass Sewers", "Yil uncovers that maintenance tunnels are acting like spell diagrams for the influx.", "Repairing the city speeds the invasion unless the repairs are morally chosen instead of mechanically efficient.", "Yil becomes responsible for deciding which parts of the city deserve power."),
    PlotArc(4, "Rookery Contradictions", 24, "Lou", "Rookery Switch", "Lou climbs the signal gantries and discovers that public fear is being tuned like radio traffic.", "Enemy behavior can be redirected, but every use of telepathic control leaves ethical residue in witnesses and controlled victims.", "Lou finds the first proof that someone human wants the mythicozoocryptids to stay."),
    PlotArc(5, "Market of False Saints", 26, "Yil", "Tin Saint Market", "The central shopping district becomes a carnival of counterfeit relics and living saint mannequins.", "Yil's salvage politics collide with black-market miracle dealers who can temporarily domesticate monsters.", "The game opens up multi-timeline trading, sabotage, and faction reputation loops."),
    PlotArc(6, "Factory Choir", 28, "Moe", "Choirburn Foundry", "Moe chases ammunition, only to find the factories are forging liturgical machine-beasts.", "The foundry leadership treats workers and monsters as interchangeable production inputs.", "Moe's pistol path evolves into a grim industrial survival campaign with heavy moral choices."),
    PlotArc(7, "Underpass Parliament", 24, "Lou", "Pilgrim Underpass", "Lou discovers encampments where humans and myth-creatures negotiate survival without the city's permission.", "Every mind-control shortcut risks destroying the only fragile diplomacy keeping the underpass from becoming a massacre.", "Lou's route becomes the social and investigative spine of the whole game."),
    PlotArc(8, "Marina of Bad Echoes", 26, "Moe", "Spite Marina", "The docks reveal a cargo route that imported reality fractures as insurance fraud.", "Moe has to choose between revenge, rescue, and burning the shipping conspiracy alive.", "Sea-adjacent horrors and flood-bosses widen the city into a nightmare coast."),
    PlotArc(9, "Reliquary Weather", 28, "Yil", "Split Reliquary", "Museum archives and saint-tech storage vaults show that the city has rehearsed this crisis before.", "Yil's magic navigation and repair abilities uncover a hidden urban cosmology built out of maintenance protocols.", "The story pivots from outbreak response to reality-governance collapse."),
    PlotArc(10, "Mutual Vacancy", 30, "Lou", "Candlelung Towers", "The apartment high-rises become a war of tenants, landlords, rescue cults, and controlled cryptids.", "Lou can keep the towers from total annihilation, but only by making ethically compromising alliances.", "This arc ties all three protagonists' private grief into the larger citywide catastrophe."),
    PlotArc(11, "Ninth Signal", 26, "All", "Ninth Station", "Every timeline converges on the transit ring where the city keeps its final shuttered observatory and largest fissure engine.", "Boss institutions openly weaponize the outbreak while the protagonists start crossing each other's routes in real time.", "The game's systems begin recombining all three traversal/combat languages."),
    PlotArc(12, "Kin Dark", 28, "All", "Ninth Station", "The final act forces the protagonists to decide what a city owes its monsters, victims, and guilty institutions once the truth can no longer be hidden.", "The last bosses are as much institutions and memories as biological enemies, and the moral endgame is survival without innocence.", "The ending resolves the three timelines into one transformed city-state or one spectacular urban ruin."),
)


GRAPHICS_COUNTS = {
    "player_animation_prefabs": 288,
    "player_story_comics": 864,
    "npc_animation_prefabs": 29_952,
    "enemy_animation_prefabs": 24_960,
    "boss_animation_prefabs": 3_456,
    "interaction_vfx_prefabs": 18_432,
    "photo_texture_panels": 21_600,
    "sprite_mesh_cards": 6_912,
    "ui_controller_map_cards": 1_536,
    "title_cinematic_save_cards": 312,
    "item_equipment_icons": 1_555,
}


AUDIO_COUNTS = {
    "looping_songs": 200,
    "combat_sfx": 512,
    "traversal_sfx": 288,
    "interaction_cues": 420,
    "ambient_stingers": 240,
    "narrative_barks": 192,
    "menu_ui": 64,
    "save_load_title": 24,
    "boss_cues": 97,
}


def ensure_dirs() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def slugify(text: str) -> str:
    return text.lower().replace(" ", "_").replace("-", "_").replace("/", "_").replace("'", "")


def protagonist_by_name(name: str) -> Protagonist:
    for protagonist in PROTAGONISTS:
        if protagonist.name == name:
            return protagonist
    return PROTAGONISTS[0]


def build_arc_pressures() -> list[dict[str, object]]:
    pressures: list[dict[str, object]] = []
    for arc in PLOT_ARCS:
        hero_index = next((index for index, hero in enumerate(PROTAGONISTS) if hero.name == arc.focus), 1)
        witness = clamp(0.32 + arc.index * 0.047 + hero_index * 0.06)
        dread = clamp(0.28 + arc.index * 0.055 + abs(math.sin(arc.index * 0.8)) * 0.18)
        myth = clamp(0.18 + arc.index * 0.061 + (0.10 if arc.index >= 8 else 0.0))
        bodily = clamp(0.24 + arc.index * 0.049 + (0.07 if arc.focus == "Moe" else 0.03))
        institution = clamp(0.22 + arc.index * 0.058 + (0.06 if arc.focus == "Lou" else 0.0))
        absurdity = clamp(0.40 + abs(math.cos(arc.index * 0.7)) * 0.32)
        closure = clamp(0.14 + arc.index * 0.068 + (0.12 if arc.index >= 10 else 0.0))
        pressures.append(
            {
                "arc": arc.index,
                "title": arc.title,
                "focus": arc.focus,
                "hours": arc.hours,
                "district": arc.district,
                "pressures": {
                    "witness_clarity": round(witness, 3),
                    "dread_pressure": round(dread, 3),
                    "myth_breach": round(myth, 3),
                    "bodily_peril": round(bodily, 3),
                    "institutional_pressure": round(institution, 3),
                    "absurdity_spark": round(absurdity, 3),
                    "closure_heat": round(closure, 3),
                },
            }
        )
    return pressures


def build_story_summary() -> dict[str, object]:
    return {
        "project": "Kin Dark",
        "format": "three-protagonist comic-noir action RPG in simulated 3D space with 2D fluid-motion sprite prefabs",
        "playtimeHours": sum(arc.hours for arc in PLOT_ARCS),
        "plotArcCount": len(PLOT_ARCS),
        "districtCount": len(DISTRICTS),
        "institutionCount": len(INSTITUTIONS),
        "bossCount": len(BOSSES),
        "protagonists": [
            {
                "name": hero.name,
                "role": hero.role,
                "combat": hero.combat_profile,
                "traversal": hero.traversal_profile,
                "animations": list(hero.animation_set),
                "signatureTools": list(hero.signature_tools),
            }
            for hero in PROTAGONISTS
        ],
        "plotArcs": [
            {
                "index": arc.index,
                "title": arc.title,
                "hours": arc.hours,
                "focus": arc.focus,
                "district": arc.district,
                "premise": arc.premise,
                "collision": arc.collision,
                "outcome": arc.outcome,
            }
            for arc in PLOT_ARCS
        ],
        "arcPressureTable": build_arc_pressures(),
        "notableNpcCount": len(NOTABLE_NPCS),
        "enemySpeciationCount": len(ENEMY_SPECIES),
    }


def render_master_book(summary: dict[str, object]) -> str:
    arc_pressure_lines = []
    for row in summary["arcPressureTable"]:
        pressures = row["pressures"]
        arc_pressure_lines.append(
            f"| {row['arc']:02d} | {row['title']} | {row['focus']} | {pressures['witness_clarity']:.3f} | {pressures['dread_pressure']:.3f} | {pressures['myth_breach']:.3f} | {pressures['bodily_peril']:.3f} | {pressures['institutional_pressure']:.3f} | {pressures['absurdity_spark']:.3f} | {pressures['closure_heat']:.3f} |"
        )

    protagonist_sections = []
    for hero in PROTAGONISTS:
        protagonist_sections.append(
            textwrap.dedent(
                f"""
                ### {hero.name}

                - Role: {hero.role}
                - Look: {hero.look}
                - Timeline premise: {hero.timeline_premise}
                - Combat lane: {hero.combat_profile}
                - Traversal lane: {hero.traversal_profile}
                - Signature tools: {", ".join(hero.signature_tools)}
                - 12-directional animation contract: {", ".join(hero.animation_set)}
                """
            ).strip()
        )

    district_lines = [f"- {title}: {direction}" for _, title, direction in DISTRICTS]
    institution_lines = [f"- {name}" for name in INSTITUTIONS]
    boss_lines = [f"- {name}" for name in BOSSES]
    npc_lines = [f"- {name}" for name in NOTABLE_NPCS]
    species_lines = [f"- {entry}" for entry in ENEMY_SPECIES]
    item_lines = [f"- {entry}" for entry in MAJOR_ITEMS]
    arc_sections = []
    for arc in PLOT_ARCS:
        arc_sections.append(
            textwrap.dedent(
                f"""
                ### Arc {arc.index:02d}: {arc.title}

                - Estimated hours: {arc.hours}
                - Focus route: {arc.focus}
                - Lead district: {arc.district}
                - Premise: {arc.premise}
                - Moral collision: {arc.collision}
                - Arc outcome: {arc.outcome}
                """
            ).strip()
        )

    arc_pressure_block = textwrap.indent("\n".join(arc_pressure_lines), "        ")
    protagonist_block = textwrap.indent("\n\n".join(protagonist_sections), "        ")
    district_block = textwrap.indent("\n".join(district_lines), "        ")
    arc_block = textwrap.indent("\n\n".join(arc_sections), "        ")
    institution_block = textwrap.indent("\n".join(institution_lines), "        ")
    boss_block = textwrap.indent("\n".join(boss_lines), "        ")
    npc_block = textwrap.indent("\n".join(npc_lines), "        ")
    species_block = textwrap.indent("\n".join(species_lines), "        ")
    item_block = textwrap.indent("\n".join(item_lines), "        ")

    return normalize_markdown(
        textwrap.dedent(
            f"""
        # Kin Dark Master Book

        ## Project Frame

        - Game: Kin Dark
        - Format: three-protagonist action RPG staged in true simulated 3D space with 2D high-definition comic-book sprite prefabs for actors and sprite-assembled 3D environment forms.
        - Tone: light-hearted gallows humor, grim urban grotesque, morally charged survival comedy.
        - Structural promise: one giant contiguous city-map hosting three intertwined timelines, with route convergence rather than isolated campaigns.
        - Total planned campaign duration: {summary['playtimeHours']} hours across {summary['plotArcCount']} arcs.

        ## ScanTide-Derived Story Engine

        Kin Dark uses a ScanTide-derived wave process rather than flat chapter outlining. Each major arc is scored across seven pressure channels:

        - witness clarity
        - dread pressure
        - myth breach
        - bodily peril
        - institutional pressure
        - absurdity spark
        - closure heat

        Those pressures are used to decide which protagonist drives the arc, how the city shifts, and where the player timelines intersect.

        | Arc | Title | Focus | Witness | Dread | Myth | Body | Institution | Absurdity | Closure |
        | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
    {arc_pressure_block}

        ## Protagonists

    {protagonist_block}

        ## World Geography

        The city is one giant nightmare metropolis, built from ruined housing, collapsed civic space, sewer infrastructure, dead factories, broken marinas, reliquary museums, and transit rings. It is expressionistically over-detailed, dense with light, moisture, soot, signage, fungus, relic junk, and artificially photographed texture surfaces mapped onto 3D model forms.

    {district_block}

        ## Plot Arcs

    {arc_block}

        ## Institutions And Boss Relationships

        The city remains governable only because mutually hostile institutions keep pretending they can contain the outbreak. Every major boss either serves one of these institutions, broke from one, or is a mythic reflection of its moral failure.

        ### Institutions

    {institution_block}

        ### Boss Lineup

    {boss_block}

        ## NPC Cast

    {npc_block}

        ## Enemy Speciation And Biology

        The mythicozoocryptids are not random monsters. They are ecological opportunists drawn to stress, secrecy, debt, ritual waste, and architectural neglect. Their biology fuses urban residue with cryptid myth, making them both comic and grotesque.

    {species_block}

        ## Systems And Timeline Rules

        - The player can begin as any protagonist, but the city timeline continues for all three.
        - Moe resolves immediate bodily danger and exposes civic abuse.
        - Yil repairs, reroutes, and re-enchants the city, which changes traversal and faction access for everyone.
        - Lou controls enemies, reads crowd intent, and opens social stealth routes other protagonists cannot access.
        - Timeline collisions rewrite future mission states, boss availability, shop inventories, rumor networks, and safe routes.
        - Every interaction has a dedicated VFX animation family and a matching systemic response class.

        ## Items, Weapons, Equipment

    {item_block}

        ## Animation, Combat, And Traversal Contract

        - Every protagonist ships with 12 unique animation sets, authored for 8-way omnidirectional facing.
        - Every NPC, enemy, and boss also resolves through omnidirectional facing, camera-relative reticle logic, and readable telegraphs.
        - Combat is real-time and controller-first.
        - The camera stays squarely behind the active protagonist, follows right-stick reticle orientation, and zooms for lock-on while LT is held.
        - Interaction is auto-contextualized onto the A button and requires a one-second hold when an interactable target is in focus.

        ## Opening Presentation

        The title screen is intentionally simple:

        - the words Kin Dark painted in rusty blood-red sketch splatter
        - a single Play Game option
        - if no save data exists, the option starts a new game immediately
        - if save data exists, the option continues from the last clean quit location

        ## Production Reality Note

        This book, plus the generated manifest stack beside it, defines the full requested scope exactly. It does not falsely claim that all {GRAPHICS_TARGET} graphical assets and {AUDIO_TARGET} audio assets have already been hand-authored in one turn. It does provide the fully generated asset program, runtime contract, and narrative book needed to move into staged production truthfully.
        """
        )
    )


def normalize_markdown(text: str) -> str:
    normalized_lines = []
    for line in text.splitlines():
        if line.startswith("    ") and len(line) > 4 and line[4] in "-|#":
            normalized_lines.append(line[4:])
            continue
        normalized_lines.append(line)
    return "\n".join(normalized_lines).strip() + "\n"


def build_runtime_spec(summary: dict[str, object]) -> str:
    protagonist_sections = []
    for hero in PROTAGONISTS:
        protagonist_sections.append(
            f"- {hero.name}: {hero.combat_profile}; traversal focus: {hero.traversal_profile}; 12 animations: {', '.join(hero.animation_set)}"
        )
    protagonist_block = textwrap.indent("\n".join(protagonist_sections), "        ")
    return normalize_markdown(
        textwrap.dedent(
            f"""
        # Kin Dark Runtime And Controller Spec

        ## Core Runtime Shape

        - simulated 3D world with 2D actor prefabs
        - one giant contiguous city map
        - three interlocking protagonist timelines active on the same world state
        - camera fixed behind the protagonist body with aim-follow reticle bias
        - real-time combat, traversal, and interaction

        ## Controller Mapping

        - Left Stick: omnidirectional movement
        - Right Stick: omnidirectional aim reticle and camera rotation bias
        - LT: zoom in, focus, and soft lock-on to object, enemy, boss, NPC, or target
        - RT: primary attack / context-fire / active power discharge
        - LB / RB: stance modifiers, spell modifiers, telepathic mode shifts, traversal assists
        - X / Y / B: combat, mobility, item use, or protagonist-specific system actions
        - A: adaptive context action; hold for 1.0 second to interact whenever interaction is available
        - View: maps, investigative overlays, timeline state, district index
        - Menu: pause, inventory, quest log, accessibility, save and quit

        ## Camera Rules

        - default camera anchor: directly behind the active protagonist, slightly elevated
        - camera orbit follows right-stick aim reticle rather than raw movement vector
        - LT focus tightens FOV and increases target stickiness
        - target lock can prioritize enemies, NPCs, interactive objects, doors, ladders, ritual devices, or evidence points

        ## Save / Boot Rules

        - opening menu is one selectable Play Game option only
        - if no save is present, Play Game launches a fresh timeline bootstrap
        - the fresh timeline bootstrap is the Dark Arrival / TweenKin First Breach tutorial slice
        - if save data is present, Play Game immediately continues the last stable checkpoint
        - checkpoints are cross-timeline and preserve district state changes caused by other protagonists

        ## Actor Prefab Contract

    {protagonist_block}

        ## Environment Contract

        - 3D city geometry assembled from sprite-built prefabs and artificially photographed surface textures
        - districts include city blocks, sewers, abandoned factories, docks, transit ruins, reliquaries, and civic towers
        - every interaction surface supports dedicated VFX and an interaction classification in the manifest

        ## Tutorial Slice Contract

        - new-game boot opens with a multi-character tutorial slice that teaches Moe, Yil, and Lou in sequence before converging them
        - the tutorial introduces Dark as a contiguous city and names the invading TweenKin as the first legible threat layer
        - movement, combat, interaction, map, and timeline state rules are taught through one shared controller grammar rather than disconnected bespoke modes
        - the tutorial exits into free-roam only after the player has used direct combat, magic traversal, telepathic manipulation, rescue interactions, and district orientation tools

        ## Title Screen Direction

        - sketchy, rusty, blood-red lettering for Kin Dark
        - blackened city silhouette and damp paper texture underlay
        - no extra menu nesting at boot
        """
        )
    )


def build_asset_overview() -> str:
    graphics_lines = [f"- {name}: {count}" for name, count in GRAPHICS_COUNTS.items()]
    audio_lines = [f"- {name}: {count}" for name, count in AUDIO_COUNTS.items()]
    graphics_block = textwrap.indent("\n".join(graphics_lines), "        ")
    audio_block = textwrap.indent("\n".join(audio_lines), "        ")
    return normalize_markdown(
        textwrap.dedent(
            f"""
        # Kin Dark Asset Program Overview

        ## Exact Requested Scope

        - Graphical assets: {GRAPHICS_TARGET}
        - Audio assets: {AUDIO_TARGET}
        - Looping songs: {SONG_TARGET}

        ## Graphics Categories

    {graphics_block}

        ## Audio Categories

    {audio_block}

        ## Manifest Notes

        - Graphics manifest format: JSON Lines at generated/kin_dark_graphics_manifest.jsonl
        - Audio manifest format: JSON Lines at generated/kin_dark_audio_manifest.jsonl
        - The graphics program includes the giant world-map model within the sprite-mesh card category.
        - The audio program includes 200 two-minute looping songs and 1,837 non-music audio assets.
        - Interaction VFX coverage is explicit rather than implied.
        """
        )
    )


def build_readme() -> str:
    return normalize_markdown(
        textwrap.dedent(
            f"""
        # Kin Dark

        Kin Dark is a new drIpTECH production foundation for a three-protagonist comic-noir urban nightmare RPG: Moe, Yil, and Lou traverse one contiguous 3D city built from sprite-prefab actors and sprite-assembled environment geometry.

        This folder does not falsely claim to contain a fully hand-authored 300-hour commercial game in one turn. It does contain a truthful production foundation built around the exact scope you asked for:

        - a generated story book using a ScanTide-derived pressure model
        - an exact-count graphics manifest with {GRAPHICS_TARGET} entries
        - an exact-count audio manifest with {AUDIO_TARGET} entries including {SONG_TARGET} two-minute loops
        - runtime and controller contracts for the behind-the-back, right-stick-reticle, controller-first 3D lane

        ## Generated Outputs

        - [generated/kin_dark_master_book.md](generated/kin_dark_master_book.md)
        - [generated/kin_dark_story_summary.json](generated/kin_dark_story_summary.json)
        - [generated/kin_dark_tutorial_slice.json](generated/kin_dark_tutorial_slice.json)
        - [generated/kin_dark_asset_summary.json](generated/kin_dark_asset_summary.json)
        - [generated/kin_dark_graphics_manifest.jsonl](generated/kin_dark_graphics_manifest.jsonl)
        - [generated/kin_dark_audio_manifest.jsonl](generated/kin_dark_audio_manifest.jsonl)
        - [generated/kin_dark_game_project.json](generated/kin_dark_game_project.json)
        - [generated/kin_dark_game_project.drip3d.json](generated/kin_dark_game_project.drip3d.json)

        ## Docs

        - [docs/KIN_DARK_GAME_BIBLE.md](docs/KIN_DARK_GAME_BIBLE.md)
        - [docs/KIN_DARK_RUNTIME_AND_CONTROLLER_SPEC.md](docs/KIN_DARK_RUNTIME_AND_CONTROLLER_SPEC.md)
        - [docs/KIN_DARK_TUTORIAL_SLICE.md](docs/KIN_DARK_TUTORIAL_SLICE.md)
        - [docs/KIN_DARK_ASSET_PROGRAM_OVERVIEW.md](docs/KIN_DARK_ASSET_PROGRAM_OVERVIEW.md)

        ## Regenerate

        Run:

        ```cmd
        build_kindark_foundation.cmd
        ```

        or:

        ```cmd
        python tools/build_kindark_foundation.py
        ```
        """
        )
    )


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_jsonl(path: Path, records) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
            count += 1
    return count


def iter_graphics_manifest():
    comic_panel_modes = [f"panel_{index:02d}" for index in range(1, 25)]
    npc_roles = [
        "clerk",
        "porter",
        "scrivener",
        "fixer",
        "medic",
        "vendor",
        "choirist",
        "lookout",
        "janitor",
        "archivist",
        "dockhand",
        "mutualist",
        "diver",
        "conductor",
        "salvager",
        "cartographer",
        "broker",
        "mechanic",
        "grim_witness",
        "fuse_keeper",
        "pawn_runner",
        "ink_driver",
        "balcony_watch",
        "court_stenographer",
        "switchyard_ratifier",
        "market_clown",
    ]
    enemy_prefixes = [
        "stamplick",
        "sumpglass",
        "radiator",
        "umbra",
        "halo",
        "brine",
        "switch",
        "dock",
        "choir",
        "ledger",
        "motel",
        "rupture",
        "signal",
        "vacancy",
        "marrow",
        "gloam",
        "silt",
        "slag",
        "feral",
        "saint",
    ]
    enemy_bodies = [
        "hound",
        "cherub",
        "mantis",
        "rook",
        "eel",
        "ape",
        "beetle",
        "gator",
        "widow",
        "ox",
        "rat",
        "colt",
        "crane",
    ]
    interaction_families = [
        "open_door",
        "kick_gate",
        "pick_lock",
        "read_notice",
        "collect_debt",
        "bind_target",
        "release_target",
        "telepathic_tag",
        "repair_junction",
        "raise_ward",
        "ignite_flare",
        "drain_valve",
        "push_cart",
        "climb_pipe",
        "swing_line",
        "vault_fence",
        "search_drawer",
        "offer_relic",
        "stabilize_rift",
        "negotiate_safehouse",
        "activate_lift",
        "decode_ledger",
        "capture_echo",
        "trigger_alarm",
    ]
    interaction_styles = [f"style_{index:02d}" for index in range(1, 9)]
    surfaces = [
        "brick",
        "tar",
        "concrete",
        "rebar",
        "mildew",
        "sheetmetal",
        "pavement",
        "plaster",
        "tile",
        "asphalt",
        "slag",
        "copper",
        "cable",
        "fungus",
        "glass",
    ]
    surface_conditions = [
        "rain",
        "soot",
        "rust",
        "flood",
        "bruise",
        "graffiti",
        "fungal",
        "oily",
        "burned",
        "moonlit",
    ]
    object_prefabs = [
        "tenement_face",
        "fire_escape_stack",
        "flood_barrier",
        "marina_crane",
        "courtbench",
        "subway_turnstile",
        "train_car",
        "billboard_frame",
        "foundry_press",
        "boiler_altar",
        "vent_cluster",
        "pipe_bridge",
        "market_shrine",
        "pawn_counter",
        "sewer_pump",
        "walkway_grate",
    ]
    ui_families = [
        "title",
        "pause",
        "map",
        "inventory",
        "district_index",
        "timeline_board",
        "reputation_board",
        "controller_glyph",
        "dialogue_frame",
        "boss_warning",
        "save_notice",
        "continue_card",
        "investigation_hud",
        "reticle_set",
        "interaction_prompt",
        "focus_overlay",
        "target_lock",
        "quest_card",
        "shop_card",
        "crafting_board",
        "death_recap",
        "journal_page",
        "photo_mode",
        "debug_capture",
    ]
    ui_contexts = [f"context_{index:02d}" for index in range(1, 9)]
    ui_states = [f"state_{index:02d}" for index in range(1, 9)]
    beat_cards = [
        "title_logo",
        "play_game_button",
        "save_resume_notice",
        "new_game_bootstrap",
        "continue_bootstrap",
        "chapter_intro",
        "chapter_outro",
        "district_arrival",
        "boss_warning",
        "investigation_reveal",
        "rumor_flash",
        "timeline_merge",
        "fissure_event",
    ]
    beat_variants = [f"variant_{index:02d}" for index in range(1, 9)]
    item_prefixes = [
        "flashlight",
        "pistol",
        "sample_case",
        "receipt",
        "wrench",
        "glyph",
        "capacitor",
        "ward",
        "lens",
        "tag",
        "relic",
        "key",
        "map",
        "tonic",
        "trinket",
        "badge",
        "mask",
        "satchel",
        "seal",
        "charm",
        "ledger",
        "coil",
        "fuse",
        "brace",
        "strap",
        "amulet",
        "notebook",
        "pass",
        "buckle",
        "filter",
        "sneaker",
    ]
    item_suffixes = [
        "basic",
        "scarred",
        "focused",
        "mythic",
        "salvaged",
        "polished",
        "grim",
        "hollow",
        "flooded",
        "cracked",
    ]
    item_views = ["icon", "equip", "inspect", "pickup", "upgrade"]

    for hero in PROTAGONISTS:
        for animation in hero.animation_set:
            for direction in DIRECTIONS:
                yield {
                    "assetId": f"{hero.slug}_{animation}_{direction}",
                    "category": "player_animation_prefabs",
                    "output": f"graphics/players/{hero.slug}/{animation}/{direction}.png",
                    "prompt": f"high-definition comicbook-style fluid-motion sprite prefab for {hero.name}, animation {animation}, facing {direction}, in Kin Dark; full-body 2D actor card for simulated 3D staging, transparent background, sharp silhouette, moody urban-noir rendering",
                }

    for hero in PROTAGONISTS:
        for arc in PLOT_ARCS:
            for panel_mode in comic_panel_modes:
                yield {
                    "assetId": f"{hero.slug}_arc_{arc.index:02d}_{panel_mode}",
                    "category": "player_story_comics",
                    "output": f"graphics/storyboards/{hero.slug}/arc_{arc.index:02d}/{panel_mode}.png",
                    "prompt": f"high-definition comicbook story panel for {hero.name} during {arc.title} in Kin Dark, district {slugify(arc.district)}, cinematic urban nightmare composition, sketch-heavy inks, expressionist detail, transparent or clean compositing layer",
                }

    for district_slug, _, direction in DISTRICTS:
        for npc_role in npc_roles:
            npc_id = f"{district_slug}_{npc_role}"
            for animation in PROTAGONISTS[0].animation_set:
                for facing in DIRECTIONS:
                    yield {
                        "assetId": f"{npc_id}_{animation}_{facing}",
                        "category": "npc_animation_prefabs",
                        "output": f"graphics/npcs/{district_slug}/{npc_id}/{animation}_{facing}.png",
                        "prompt": f"Kin Dark NPC sprite prefab for {npc_role.replace('_', ' ')} from {district_slug.replace('_', ' ')}, animation {animation}, facing {facing}, comic-noir urban survivor style, transparent background, fluid-motion pose, district direction: {direction}",
                    }

    for prefix in enemy_prefixes:
        for body in enemy_bodies:
            species_id = f"{prefix}_{body}"
            for animation in PROTAGONISTS[0].animation_set:
                for facing in DIRECTIONS:
                    yield {
                        "assetId": f"{species_id}_{animation}_{facing}",
                        "category": "enemy_animation_prefabs",
                        "output": f"graphics/enemies/{species_id}/{animation}_{facing}.png",
                        "prompt": f"Kin Dark mythicozoocryptid enemy prefab for {prefix} {body}, animation {animation}, facing {facing}, high-definition comicbook sprite card, grotesque yet readable silhouette, transparent background, fluid-motion urban horror staging",
                    }

    boss_states = [f"phase_{phase:02d}_state_{state:02d}" for phase in range(1, 4) for state in range(1, 7)]
    for boss in BOSSES:
        boss_slug = slugify(boss)
        for state in boss_states:
            for facing in DIRECTIONS:
                yield {
                    "assetId": f"{boss_slug}_{state}_{facing}",
                    "category": "boss_animation_prefabs",
                    "output": f"graphics/bosses/{boss_slug}/{state}_{facing}.png",
                    "prompt": f"Kin Dark boss sprite prefab for {boss}, state {state}, facing {facing}, extravagant dark expressionist comic illustration, transparent background, oversized telegraph-friendly silhouette, 2D actor card for simulated 3D arena staging",
                }

    for district_slug, _, direction in DISTRICTS:
        for interaction in interaction_families:
            for style in interaction_styles:
                for facing in DIRECTIONS:
                    yield {
                        "assetId": f"{district_slug}_{interaction}_{style}_{facing}",
                        "category": "interaction_vfx_prefabs",
                        "output": f"graphics/vfx/{district_slug}/{interaction}/{style}_{facing}.png",
                        "prompt": f"Kin Dark interaction VFX animation card for {interaction.replace('_', ' ')} in {district_slug.replace('_', ' ')}, style {style}, facing {facing}, lush dark comicbook energy, transparent background, readable gameplay effect",
                    }

    for district_slug, _, direction in DISTRICTS:
        for surface in surfaces:
            for condition in surface_conditions:
                family = f"{surface}_{condition}"
                for variant in range(1, 13):
                    yield {
                        "assetId": f"{district_slug}_{family}_{variant:02d}",
                        "category": "photo_texture_panels",
                        "output": f"graphics/textures/{district_slug}/{family}_{variant:02d}.png",
                        "prompt": f"artificially generated photograph of {surface} under {condition} treatment for Kin Dark district {district_slug.replace('_', ' ')}, usable as texture source on 3D sprite-built geometry, dark urban nightmare detail, district direction: {direction}",
                    }

    master_map_assigned = False
    for district_slug, _, direction in DISTRICTS:
        for prefab in object_prefabs:
            for variant in range(1, 7):
                object_slug = f"{prefab}_{variant:02d}"
                if not master_map_assigned:
                    object_slug = "world_master_map_model"
                    master_map_assigned = True
                for angle in MESH_ANGLES:
                    yield {
                        "assetId": f"{district_slug}_{object_slug}_{angle}",
                        "category": "sprite_mesh_cards",
                        "output": f"graphics/mesh_cards/{district_slug}/{object_slug}_{angle}.png",
                        "prompt": f"Kin Dark sprite-built 3D mesh card for {object_slug.replace('_', ' ')} in {district_slug.replace('_', ' ')}, view {angle}, expressionist comic detail, transparent background or clean card layer, district direction: {direction}",
                    }

    for family in ui_families:
        for context in ui_contexts:
            for state in ui_states:
                yield {
                    "assetId": f"{family}_{context}_{state}",
                    "category": "ui_controller_map_cards",
                    "output": f"graphics/ui/{family}/{context}_{state}.png",
                    "prompt": f"Kin Dark UI asset for {family.replace('_', ' ')}, {context}, {state}, blood-red sketch noir styling, controller-first readability, transparent background, production-ready HUD/menu card",
                }

    card_total = 0
    while card_total < GRAPHICS_COUNTS["title_cinematic_save_cards"]:
        beat = beat_cards[card_total % len(beat_cards)]
        variant = beat_variants[(card_total // len(beat_cards)) % len(beat_variants)]
        sequence = card_total // (len(beat_cards) * len(beat_variants))
        yield {
            "assetId": f"{beat}_{variant}_set_{sequence:02d}_{card_total:03d}",
            "category": "title_cinematic_save_cards",
            "output": f"graphics/title_and_cinematics/{sequence:02d}/{beat}_{variant}_{card_total:03d}.png",
            "prompt": f"Kin Dark title, save, or cinematic card for {beat.replace('_', ' ')}, {variant}, rusty blood-red sketch splatter, comic-noir city backdrop, controller-first menu clarity",
        }
        card_total += 1

    item_index = 0
    for prefix in item_prefixes:
        for suffix in item_suffixes:
            if item_index >= 311:
                break
            item_family = f"{prefix}_{suffix}"
            for view in item_views:
                yield {
                    "assetId": f"{item_family}_{view}",
                    "category": "item_equipment_icons",
                    "output": f"graphics/items/{item_family}/{view}.png",
                    "prompt": f"Kin Dark item icon for {prefix.replace('_', ' ')} {suffix}, view {view}, high-definition comicbook prop render, transparent background, dark lavish detailing",
                }
            item_index += 1
        if item_index >= 311:
            break
    yield {
        "assetId": "keystone_ledger_icon",
        "category": "item_equipment_icons",
        "output": "graphics/items/keystone_ledger/icon.png",
        "prompt": "Kin Dark special item icon for the Keystone Ledger, transparent background, grim comic-noir prop render",
    }
    yield {
        "assetId": "keystone_ledger_equip",
        "category": "item_equipment_icons",
        "output": "graphics/items/keystone_ledger/equip.png",
        "prompt": "Kin Dark special equip card for the Keystone Ledger, transparent background, grim comic-noir prop render",
    }
    yield {
        "assetId": "keystone_ledger_inspect",
        "category": "item_equipment_icons",
        "output": "graphics/items/keystone_ledger/inspect.png",
        "prompt": "Kin Dark inspect card for the Keystone Ledger, transparent background, grim comic-noir prop render",
    }
    yield {
        "assetId": "keystone_ledger_pickup",
        "category": "item_equipment_icons",
        "output": "graphics/items/keystone_ledger/pickup.png",
        "prompt": "Kin Dark pickup card for the Keystone Ledger, transparent background, grim comic-noir prop render",
    }
    yield {
        "assetId": "keystone_ledger_upgrade",
        "category": "item_equipment_icons",
        "output": "graphics/items/keystone_ledger/upgrade.png",
        "prompt": "Kin Dark upgrade card for the Keystone Ledger, transparent background, grim comic-noir prop render",
    }


def iter_audio_manifest():
    song_styles = [
        "rusty_noir",
        "drain_choir",
        "sewer_lullaby",
        "factory_liturgy",
        "marina_static",
        "fissure_cabaret",
        "tenement_jazz",
        "reliquary_dirge",
        "signal_waltz",
        "panic_boogie",
        "tram_requiem",
        "afterhours_organ",
        "cryptid_samba",
        "boiler_psalm",
        "moonlit_siren",
        "ledger_fugue",
    ]
    track_index = 0
    for district_slug, _, _ in DISTRICTS:
        for style in song_styles:
            if track_index >= SONG_TARGET - 8:
                break
            yield {
                "assetId": f"song_{track_index + 1:03d}_{district_slug}_{style}",
                "category": "looping_songs",
                "output": f"audio/music/{district_slug}/{style}.wav",
                "durationSeconds": 120,
                "prompt": f"two-minute looping Kin Dark song for {district_slug.replace('_', ' ')} in style {style.replace('_', ' ')}, true-instrument synth palette, urban nightmare atmosphere, memorable melodic identity",
            }
            track_index += 1
    while track_index < SONG_TARGET:
        yield {
            "assetId": f"song_{track_index + 1:03d}_timeline_merge_{track_index - (SONG_TARGET - 8) + 1:02d}",
            "category": "looping_songs",
            "output": f"audio/music/timeline_merge/merge_{track_index - (SONG_TARGET - 8) + 1:02d}.wav",
            "durationSeconds": 120,
            "prompt": "two-minute looping Kin Dark convergence theme for merged protagonist timelines, lush synth instrumentation, comic-noir dread with hopeful motion",
        }
        track_index += 1

    combat_moves = [
        "moe_quickdraw",
        "moe_pistol_fire",
        "moe_reload",
        "moe_flashlight_bash",
        "yil_sigil_burst",
        "yil_blink_step",
        "yil_ward_raise",
        "yil_overload",
        "lou_mark",
        "lou_puppet",
        "lou_release",
        "lou_psychic_snap",
        "cryptid_bite",
        "cryptid_slam",
        "boss_charge",
        "boss_phase_shift",
        "dodge_close",
        "parry_glint",
        "stagger_hit",
        "critical_finish",
        "fissure_burst",
        "anomaly_scratch",
        "panic_surge",
        "lock_on_confirm",
        "charge_release",
        "boiler_smash",
        "signal_whine",
        "claw_rake",
        "tail_thrash",
        "sump_splash",
        "muzzle_echo",
        "telepathic_feedback",
        "chain_impact",
        "ward_break",
        "reality_tear",
        "ghost_lunge",
        "roofdrop",
        "pipe_crack",
        "saint_howl",
        "ledger_whip",
        "anchor_slam",
        "gavel_stomp",
        "rail_spark",
        "dock_blast",
        "tram_shunt",
        "foundry_roar",
        "gear_shriek",
        "panic_reload",
        "flare_pop",
        "ritual_spike",
        "mote_swarm",
        "hook_snag",
        "flood_breach",
        "vacancy_bell",
        "reticle_snap",
        "coil_discharge",
        "sneaker_kick",
        "ceiling_pounce",
        "monkey_chatter_control",
        "divorce_file_rip",
        "crane_drop",
        "choir_bellow",
        "sump_moan",
        "halo_burst",
    ]
    for move in combat_moves:
        for variant in range(1, 9):
            yield {
                "assetId": f"{move}_v{variant:02d}",
                "category": "combat_sfx",
                "output": f"audio/sfx/combat/{move}_v{variant:02d}.wav",
                "durationSeconds": round(0.25 + variant * 0.03, 3),
                "prompt": f"Kin Dark combat SFX for {move.replace('_', ' ')}, variant {variant}, punchy real-time mix, controller-responsive attack readability",
            }

    traversal_moves = [
        "walk_puddle",
        "walk_grit",
        "walk_rebar",
        "run_concrete",
        "run_grate",
        "run_rooftop",
        "climb_pipe",
        "climb_brick",
        "ceiling_traverse",
        "vault_railing",
        "jump_short",
        "jump_heavy",
        "land_soft",
        "land_hard",
        "ladder_slide",
        "blink_depart",
        "blink_arrive",
        "glide_rune",
        "telepathic_hop",
        "rope_swing",
        "duck_vent",
        "crawl_duct",
        "push_door",
        "shove_gate",
        "tightrope_step",
        "wade_sump",
        "elevator_start",
        "elevator_stop",
        "dock_chain",
        "fire_escape_rattle",
        "train_roof_scrape",
        "fence_slide",
        "drain_drop",
        "mural_ledge",
        "signal_perch",
        "panic_sprint",
    ]
    for move in traversal_moves:
        for variant in range(1, 9):
            yield {
                "assetId": f"{move}_v{variant:02d}",
                "category": "traversal_sfx",
                "output": f"audio/sfx/traversal/{move}_v{variant:02d}.wav",
                "durationSeconds": round(0.18 + variant * 0.02, 3),
                "prompt": f"Kin Dark traversal SFX for {move.replace('_', ' ')}, variant {variant}, tactile movement cue for controller-first behind-the-back play",
            }

    interaction_names = [
        "hold_interact",
        "open_safehouse",
        "activate_lift",
        "decode_ledger",
        "turn_valve",
        "loot_cache",
        "read_notice",
        "talk_prompt",
        "threaten_prompt",
        "bribe_prompt",
        "telepathic_probe",
        "release_control",
        "stabilize_fissure",
        "repair_panel",
        "craft_station",
        "shop_confirm",
        "relic_insert",
        "boss_gate",
        "district_arrival",
        "save_point",
        "continue_point",
        "rumor_capture",
        "evidence_tag",
        "route_unlock",
        "ward_charge",
        "ward_release",
        "motel_checkin",
        "court_file_open",
        "floodlock_release",
        "dock_crane_call",
        "subway_map_open",
        "elevator_access",
        "reputation_update",
        "quest_accept",
        "quest_complete",
    ]
    for district_slug, _, _ in DISTRICTS:
        for interaction in interaction_names:
            yield {
                "assetId": f"{district_slug}_{interaction}",
                "category": "interaction_cues",
                "output": f"audio/sfx/interaction/{district_slug}/{interaction}.wav",
                "durationSeconds": 0.65,
                "prompt": f"Kin Dark interaction cue for {interaction.replace('_', ' ')} in {district_slug.replace('_', ' ')}, clear game-state communication with dark comic character",
            }

    ambient_moods = [
        "rain_hum",
        "sewer_echo",
        "factory_drift",
        "marina_rope",
        "court_fluorescent",
        "transit_singal",
        "distant_riot",
        "cryptid_chatter",
        "pigeon_burst",
        "drain_whistle",
        "neon_buzz",
        "tower_creak",
        "motel_vent",
        "museum_static",
        "fissure_breath",
        "choir_underlay",
        "hallway_drip",
        "street_thunder",
        "tram_resonance",
        "night_siren",
    ]
    for district_slug, _, _ in DISTRICTS:
        for mood in ambient_moods:
            yield {
                "assetId": f"{district_slug}_{mood}",
                "category": "ambient_stingers",
                "output": f"audio/ambient/{district_slug}/{mood}.wav",
                "durationSeconds": 6.0,
                "prompt": f"Kin Dark ambient stinger for {district_slug.replace('_', ' ')} mood {mood.replace('_', ' ')}, lush urban nightmare texture",
            }

    bark_states = ["calm", "uneasy", "joking", "urgent", "shaken", "resolved", "grim", "spent"]
    bark_variants = [f"take_{index:02d}" for index in range(1, 9)]
    for hero in PROTAGONISTS:
        for state in bark_states:
            for variant in bark_variants:
                yield {
                    "assetId": f"{hero.slug}_{state}_{variant}",
                    "category": "narrative_barks",
                    "output": f"audio/voice/{hero.slug}/{state}_{variant}.wav",
                    "durationSeconds": 1.8,
                    "prompt": f"Kin Dark narrative bark for {hero.name}, emotional state {state}, {variant}, expressive comic-noir voice cue",
                }

    menu_events = [
        "cursor_move",
        "cursor_confirm",
        "cursor_back",
        "menu_open",
        "menu_close",
        "tab_shift",
        "map_open",
        "map_close",
        "save_ready",
        "save_commit",
        "load_resume",
        "journal_flip",
        "quest_pin",
        "reticle_focus",
        "target_cycle",
        "warning_flash",
    ]
    for event in menu_events:
        for variant in range(1, 5):
            yield {
                "assetId": f"{event}_v{variant:02d}",
                "category": "menu_ui",
                "output": f"audio/ui/{event}_v{variant:02d}.wav",
                "durationSeconds": 0.35,
                "prompt": f"Kin Dark menu or UI sound for {event.replace('_', ' ')}, variant {variant}, clean and readable controller UX feedback",
            }

    save_events = ["title_appear", "play_press", "new_game_boot", "continue_boot", "save_suspend", "save_resume"]
    for event in save_events:
        for variant in range(1, 5):
            yield {
                "assetId": f"{event}_v{variant:02d}",
                "category": "save_load_title",
                "output": f"audio/title/{event}_v{variant:02d}.wav",
                "durationSeconds": 0.9,
                "prompt": f"Kin Dark title or save-state cue for {event.replace('_', ' ')}, variant {variant}, rusty blood-red sketch menu mood",
            }

    for boss in BOSSES:
        boss_slug = slugify(boss)
        for phase in range(1, 5):
            yield {
                "assetId": f"{boss_slug}_phase_{phase:02d}",
                "category": "boss_cues",
                "output": f"audio/boss/{boss_slug}/phase_{phase:02d}.wav",
                "durationSeconds": 4.5,
                "prompt": f"Kin Dark boss transition cue for {boss}, phase {phase}, dramatic but game-readable stinger",
            }
    yield {
        "assetId": "final_city_rupture",
        "category": "boss_cues",
        "output": "audio/boss/final_city_rupture.wav",
        "durationSeconds": 7.5,
        "prompt": "Kin Dark final city rupture sting, endgame convergence of myth, institution, and urban collapse",
    }


def build_runtime_contract(summary: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    protagonists_json = []
    for hero in PROTAGONISTS:
        protagonists_json.append(
            {
                "id": hero.slug,
                "display_name": hero.name,
                "role": hero.role,
                "look": hero.look,
                "combat_profile": hero.combat_profile,
                "traversal_profile": hero.traversal_profile,
                "asset_prefix": f"graphics/players/{hero.slug}",
                "animations": [
                    {
                        "name": animation,
                        "directions": DIRECTIONS,
                        "prefab_pattern": f"graphics/players/{hero.slug}/{animation}/{{direction}}.png",
                    }
                    for animation in hero.animation_set
                ],
                "signature_tools": list(hero.signature_tools),
            }
        )

    game_project = {
        "project_name": "Kin Dark",
        "project_type": "comic_noir_sprite_3d_action_rpg",
        "seed": "KIN-DARK-FOUNDATION",
        "design_intent": "three intertwined protagonist timelines on one giant urban nightmare map",
        "story_book": str(MASTER_BOOK_PATH.relative_to(ROOT)).replace("\\", "/"),
        "tutorial_slice": str(TUTORIAL_SUMMARY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "asset_summary": str(ASSET_SUMMARY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "graphics_manifest": str(GRAPHICS_MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
        "audio_manifest": str(AUDIO_MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
        "playtime_hours": summary["playtimeHours"],
        "protagonists": protagonists_json,
        "world": {
            "map_type": "single_contiguous_city",
            "districts": [
                {
                    "id": slug,
                    "title": title,
                    "direction": direction,
                }
                for slug, title, direction in DISTRICTS
            ],
            "institutions": list(INSTITUTIONS),
            "bosses": list(BOSSES),
        },
        "camera": {
            "mode": "behind_player",
            "aim_driver": "right_stick_reticle",
            "movement_driver": "left_stick",
            "focus_lock_button": "LT",
            "focus_lock_behavior": "zoom_and_soft_lock",
        },
        "input": {
            "primary": "xbox_series_controller",
            "mapping": {
                "move": "left_stick",
                "aim": "right_stick",
                "focus_lock": "LT",
                "primary_attack": "RT",
                "action_cluster": ["LB", "RB", "X", "Y", "B"],
                "interact": "hold_A_1_second_when_available",
                "map": "View",
                "menu": "Menu",
            },
        },
        "boot": {
            "title_screen": {
                "logo_style": "rusty blood-red sketch splatter",
                "menu_options": ["play_game"],
                "no_save_behavior": "new_game_tutorial_slice",
                "save_present_behavior": "continue_last_quit",
            },
            "new_game_sequence": "dark_arrival_tweenkin_first_breach",
        },
        "systems": {
            "real_time": True,
            "vfx_for_every_interaction": True,
            "timeline_state_shared": True,
            "prefab_actor_pipeline": True,
            "photo_texture_environment": True,
            "tutorial_slice": True,
        },
    }

    drip3d_project = {
        "project_name": "KinDark",
        "driptech_scene_version": "1.0",
        "translation_profile": {
            "art_export": "depth_mapped_2d_prefab_cards",
            "blender": "sprite_assembled_city_mesh",
            "engine": "behind_back_controller_runtime",
        },
        "camera_profile": {
            "anchor": "behind_player",
            "right_stick_reticle": True,
            "lt_focus_zoom": True,
            "soft_lock_targets": ["enemy", "boss", "npc", "object", "evidence"],
        },
        "bindings": {
            "player_symbols": [hero.slug for hero in PROTAGONISTS],
            "district_symbols": [slug for slug, _, _ in DISTRICTS],
            "script_bindings": [
                {"event": "title_play_game", "command": "continue_or_new_game"},
                {"event": "interaction_available", "command": "swap_A_to_hold_interact"},
                {"event": "lt_focus", "command": "camera_zoom_soft_lock"},
            ],
        },
        "bridges": {
            "art_export": {
                "timeline_fps": 12,
                "sprite_card_usage": "all_actors_and_interaction_vfx",
            },
            "blender": {
                "world_mesh": "single_city_map",
                "environment_cards": "sprite_assembled_3d_shapes",
                "texture_source": "artificial_photograph_panels",
            },
            "engine": {
                "entry_scene": "title_screen",
                "controller_profile": "xbox_series_default",
                "save_rule": "continue_if_save_else_new",
            },
        },
    }
    return game_project, drip3d_project


def build_asset_summary(graphics_written: int, audio_written: int) -> dict[str, object]:
    if graphics_written != GRAPHICS_TARGET:
        raise RuntimeError(f"Expected {GRAPHICS_TARGET} graphics entries, wrote {graphics_written}")
    if audio_written != AUDIO_TARGET:
        raise RuntimeError(f"Expected {AUDIO_TARGET} audio entries, wrote {audio_written}")
    return {
        "project": "Kin Dark",
        "graphicsTarget": GRAPHICS_TARGET,
        "graphicsWritten": graphics_written,
        "graphicsCategories": GRAPHICS_COUNTS,
        "audioTarget": AUDIO_TARGET,
        "audioWritten": audio_written,
        "audioCategories": AUDIO_COUNTS,
        "loopingSongs": SONG_TARGET,
        "worldMapIncluded": True,
        "notes": [
            "Manifest entries are fully generated and exact-count.",
            "This stack defines production scope truthfully rather than claiming all art and audio are already hand-authored.",
            "Interaction VFX are explicitly allocated across all district/interaction classes.",
        ],
    }


def main() -> int:
    ensure_dirs()

    summary = build_story_summary()
    tutorial_slice = build_tutorial_slice()
    master_book = render_master_book(summary)
    runtime_spec = build_runtime_spec(summary)
    asset_overview = build_asset_overview()
    tutorial_markdown = render_tutorial_slice_markdown(tutorial_slice)

    MASTER_BOOK_PATH.write_text(master_book, encoding="utf-8")
    GAME_BIBLE_PATH.write_text(master_book, encoding="utf-8")
    RUNTIME_SPEC_PATH.write_text(runtime_spec, encoding="utf-8")
    ASSET_OVERVIEW_PATH.write_text(asset_overview, encoding="utf-8")
    TUTORIAL_SLICE_PATH.write_text(tutorial_markdown, encoding="utf-8")
    README_PATH.write_text(build_readme(), encoding="utf-8")
    write_json(STORY_SUMMARY_PATH, summary)
    write_json(TUTORIAL_SUMMARY_PATH, tutorial_slice)

    graphics_written = write_jsonl(GRAPHICS_MANIFEST_PATH, iter_graphics_manifest())
    audio_written = write_jsonl(AUDIO_MANIFEST_PATH, iter_audio_manifest())
    asset_summary = build_asset_summary(graphics_written, audio_written)
    write_json(ASSET_SUMMARY_PATH, asset_summary)
    write_json(GRAPHICS_SUMMARY_PATH, {"graphicsWritten": graphics_written, "graphicsCategories": GRAPHICS_COUNTS})

    game_project, drip3d_project = build_runtime_contract(summary)
    write_json(GAME_PROJECT_PATH, game_project)
    write_json(DRIP3D_PROJECT_PATH, drip3d_project)

    print(json.dumps({
        "story_book": str(MASTER_BOOK_PATH),
        "graphics_manifest": str(GRAPHICS_MANIFEST_PATH),
        "audio_manifest": str(AUDIO_MANIFEST_PATH),
        "asset_summary": str(ASSET_SUMMARY_PATH),
        "graphics_written": graphics_written,
        "audio_written": audio_written,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())