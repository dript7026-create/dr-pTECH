# ArchesAndAngels NanoPlay_t and PlayHub Strategy

## Scope

This document frames two product tracks for `ArchesAndAngels: Sinner of Oblivion`:

- `NanoPlay_t`: a premium but budget-disciplined handheld-first version built around tactile strategic play, short-session traversal, and on-device campaign persistence.
- `PlayHub / DripDungeons`: a lower-risk PC-and-controller-first version that compresses the setting into replayable dungeon campaigns, extraction loops, and faction-driven runs.

This is a planning document, not legal, lending, accounting, or securities advice. It is intentionally bounded to lawful business formation, product execution, supply-chain realism, and ethical publishing. It does not propose political manipulation, military planning, coercive social control, or unlawful financial activity.

## Product Split

### NanoPlay_t

Positioning:
`ArchesAndAngels` as a tactile strategic action-RPG device experience where the city simulation, district maps, mission board, and moment-to-moment traversal live in one portable machine.

Core play pillars:

- weekly civic command layer with physical-feeling haptics tied to pressure, worship, and vice states
- top-down field missions that resolve the strategic map through authored infiltration, escort, and ritual disruption scenarios
- asymmetric input use: left-stick movement, right-stick combat aim, shoulder-layer district command shortcuts, gyro-assisted relic targeting
- offline-first campaign persistence with low-friction suspend/resume and deterministic seeds for event auditing

Target device spec for a 1,000-unit prototype run:

- 5.5 inch to 6 inch 720p display
- ARM-based Linux handheld platform using an off-the-shelf compute module or mature SBC family, not a fully custom SoC
- 6 GB to 8 GB RAM
- 64 GB eMMC minimum
- hall-effect sticks, standard d-pad, four face buttons, four shoulder inputs
- gyro, rumble, Wi‑Fi, USB-C power/data/video-out
- battery sized for 4 to 5 hours real play under capped performance mode
- custom launcher shell over Linux, not a fully custom OS fork

Practical firmware and OS stance:

- use a locked-down Linux distro with a read-only system partition and an updateable game/content partition
- use SDL or a similar portable input layer for parity with the PlayHub build
- avoid a fresh kernel fork unless manufacturing partner support requires it
- scope over-the-air updates, crash telemetry opt-in, and save export only after the first playable hardware sprint

Why this is viable:

- 1,000 units inside a total project budget of 120,000 to 350,000 dollars is only realistic with off-the-shelf internals, modest industrial design, and a limited certification footprint
- a true custom console stack would exceed the upper budget band before content and manufacturing reserves are funded

### PlayHub / DripDungeons

Positioning:
`DripDungeons_ArchesAndAngels` as the faster-to-market and lower-capex product. It converts the world into a repeatable run-based dungeon strategy game with stronger extraction loops and social sharing.

Core play pillars:

- district-specific dungeon runs derived from the sim state and scenario cards
- party assembly from protagonists, operatives, and faction defectors
- short-run progression with relic extraction, shrine disruption, vice-market routing, and covenant choices
- couch-controller support and PC-first distribution for earliest revenue validation
- shared fiction and asset pipeline with NanoPlay_t to avoid duplicated worldbuilding cost

Platform stance:

- Windows first, Linux second
- gamepad mandatory, mouse and keyboard optional
- cloud sync optional, not required for launch
- mod-safe data layer for mission tables, event text, enemy loadouts, and district scenario rules

## Next-Next-Next-Gen Experience Within Indie Constraints

The credible version of "next-gen" at this budget is not photorealism. It is systemic density, input feel, and continuity between strategic and embodied play.

Deliverable innovations that fit the budget:

- one canonical simulation driving both strategy and mission generation
- district scenario successor chains that reshape traversal and enemy composition in visible ways
- diegetic handheld UX where battery, haptics, and sound design reinforce the merged city-state fantasy
- high reactivity in authored spaces rather than huge empty worlds
- mission reassembly from scenario pressure, agenda urgency, and protagonist trust rather than from static quest lists

Avoid at prototype stage:

- custom silicon
- bespoke online infrastructure beyond patch delivery and optional telemetry
- full cloud streaming dependency
- multi-region certification before the product-market fit checkpoint

## Hardware Budget Model

### Loan Framing

Requested capital envelope:

- lower band: 120,000 dollars
- target band: 220,000 to 280,000 dollars
- upper defensive band: 350,000 dollars

Debt consolidation constraint acknowledged:

- approximately 35,000 dollars of existing unsecured debt can be treated as part of the financing plan only if the lending structure, business formation, and personal guarantees are reviewed by qualified counsel and a licensed accountant
- operational planning below assumes that debt consolidation is ring-fenced from project burn reporting so product capital is not confused with cleanup capital

### Recommended Allocation at 260,000 Dollars

- 35,000 debt consolidation reserve
- 18,000 incorporation, accounting, legal formation, contract review, trademark filing, and lender compliance
- 22,000 hardware engineering, EVT support, enclosure iteration, and manufacturing liaison work
- 118,000 first 1,000-unit hardware prototype batch including components, assembly, packaging, and freight buffer
- 26,000 game development payroll reserve for contract art, audio, tools, and engineering support
- 9,000 QA, test fixtures, replacement parts, and failure analysis
- 8,000 certification pre-checks, import/export paperwork, and safety documentation
- 12,000 marketing foundation, landing page, trailers, vertical slice capture, and demo event costs
- 12,000 contingency reserve

### Unit Economics for NanoPlay_t Prototype Run

Indicative target, not a vendor quote:

- electronics BOM: 95 to 125 dollars per unit
- shell, buttons, assembly: 18 to 28 dollars per unit
- display and battery: 24 to 36 dollars per unit
- packaging and accessories: 8 to 14 dollars per unit
- freight, scrap, rework reserve: 12 to 22 dollars per unit

Expected landed prototype cost target:

- approximately 157 to 225 dollars per unit before overhead allocation

That supports a 1,000-unit prototype run if industrial design, firmware complexity, and compliance scope remain disciplined.

## Parallel Business Plan

### Track A: Immediate Revenue Validation

- ship PlayHub / DripDungeons first as the lower-capex software product
- use the same world data, writing bible, scenario system, and combat prototype as NanoPlay_t
- validate retention, wishlist conversion, and audience fit before expanding hardware exposure

### Track B: Hardware Proof

- build a devkit-like NanoPlay_t pilot around a stable compute module and pre-certified radios
- reserve the first 100 to 150 units for QA, partners, press, lenders, and controlled community pilots
- keep the remaining units for founders edition sales, demo deployment, and structured field feedback

### Track C: Corporate Structure

- parent entity: Do9 or drIpTECH parent business once counsel confirms tax and liability posture
- product IP and publishing contracts isolated in a subsidiary or protected operating unit if affordable
- hardware procurement and warranty obligations separated from content contracting wherever possible

## Future-Proofing Domains

### Finance and economics

- keep hardware and software P&L separate from the first day of bookkeeping
- model best case, base case, and failure case monthly cashflow
- treat hardware as risk capital and software as the first operating-revenue engine
- avoid counting preorders as available cash until refund liabilities are reserved

### Ethical and social posture

- publish a clear content and community policy for adult themes, body politics, narcotics, and religion in the fiction
- collect only minimal player telemetry with explicit consent
- plan accessibility from the first playable milestone: remapping, subtitles, text scaling, color separation, and simplified input presets

### Legal and regulatory posture

- use counsel for lending review, incorporation, consumer hardware terms, privacy policy, export classification, and refund language
- secure rights chain for all art, audio, contractors, and middleware
- do not ship unlicensed wireless hardware or non-compliant chargers

### Geographic and supply-chain posture

- use at least two component sourcing paths for displays, batteries, and sticks
- assume freight delays and customs holds in the budget
- support both urban and rural usage with offline-first play, low-bandwidth patching, and USB sideload recovery

### Cultural and market posture

- position the fiction as high-density worldbuilding and systems design, not shock-value branding alone
- localize store copy and key UI strings before attempting broad international reach
- test whether the audience responds more strongly to the strategic sim identity or the dungeon-run identity, then market accordingly

### Environmental and planetary posture

- minimize plastic revisions by settling the shell early
- provide replaceable batteries if manufacturing partner capability allows it
- use small-run packaging with low-ink print and minimal non-recyclable inserts

### Security and resilience posture

- harden patch signing and content packaging
- maintain an RMA reserve and spare-parts stock for the prototype run
- build recovery images and a simple reflashing workflow before shipping hardware pilots

## Milestone Path

### Phase 1: 0 to 3 months

- complete the shared simulation and mission-generation core
- ship a PC prototype of PlayHub / DripDungeons internally
- produce lender-ready financial model and formation checklist

### Phase 2: 4 to 6 months

- vertical slice for NanoPlay_t input, suspend/resume, and battery profile
- first hardware partner quotes and enclosure feasibility review
- public-facing PlayHub demo and wishlist campaign

### Phase 3: 7 to 12 months

- first pilot hardware batch
- external QA and controlled community test program
- decide whether to expand NanoPlay_t manufacturing or keep it as a premium limited platform while PlayHub remains the mainline business

## Decision Rules

- if PlayHub does not show early demand, do not scale hardware beyond pilot quantities
- if hardware costs exceed the upper band, freeze custom industrial design and reuse existing shells or controller platforms
- if lender terms require unsafe personal exposure, reduce scope and prioritize software-first launch

## Bottom Line

The realistic path is:

- use PlayHub / DripDungeons as the first revenue and audience-validation product
- use NanoPlay_t as a disciplined premium hardware experiment built on existing Linux handheld architecture
- keep the total first financing ask in a defensible range near 220,000 to 280,000 dollars unless manufacturing quotes prove otherwise
- isolate debt cleanup, operating reserve, and hardware capex so the business can be judged on actual product performance rather than blended personal financial stress