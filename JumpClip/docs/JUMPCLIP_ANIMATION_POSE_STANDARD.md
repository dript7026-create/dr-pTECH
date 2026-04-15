# JumpClip Animation And Key-Pose Standard

## Purpose

This document defines a practical animation grammar for JumpClip outputs so generated sprite sheets can be directed with consistent key-pose logic rather than vague motion prompts.

## Core Motion Rule

Every animation should communicate intention through a small number of decisive poses.

The minimum readable chain is:

- preparation
- commitment
- contact or apex
- recovery

If a move does not read through those states, add fewer inbetweens and stronger pose contrast before adding more frames.

## Pose Stack

Each JumpClip animation should be designed across these layers:

- root or pelvis motion
- torso angle and compression
- head or gaze orientation
- lead limb action
- trailing limb follow-through
- prop or weapon line
- secondary motion

## Motion Families

JumpClip should classify character motion into a few readable families.

### Grounded

- clear compression before movement
- visible foot contact
- slower recovery
- lower center of mass

### Agile

- stronger directional lean
- shorter contact time
- sharper reversal poses
- greater limb spread at apex frames

### Floaty

- delayed vertical settle
- reduced visible impact
- offset follow-through on cloth, hair, or ornament
- stronger anticipation in upper body than lower body

### Brutal

- large anticipation
- short violent travel phase
- exaggerated overshoot
- delayed recoil or recoil stutter

### Ritual

- sustained holds
- symmetrical or deliberately staged hand shapes
- slower acceleration
- more importance on gaze and upper torso choreography

## Required Key Poses By Animation Type

### Idle

- neutral stance
- weight-shift variant
- breath expansion or contraction
- scan or focus cue

### Walk

- contact left
- passing left
- contact right
- passing right

### Run

- load pose
- airborne extension
- impact pose
- recoil or gather pose

### Jump Arc

- crouch or launch preparation
- launch
- apex
- descent
- landing compression
- landing recovery

### Melee Strike

- anticipation coil
- release path
- impact or extension
- follow-through
- reset or guard return

### Cast Or Ability Gesture

- gather or invoke
- release cue
- peak silhouette or channel frame
- discharge or collapse
- composure return

### Hit React

- pre-hit neutral
- hit direction displacement
- collapse or brace
- recover or stagger continuation

### Death Or Defeat

- destabilization
- major directional fall or buckle
- ground or terminal pose
- settle

## Pose Readability Rules

- one limb should lead the action clearly
- hands and feet should not merge into the torso silhouette at important frames
- head orientation should reinforce intent before the body fully commits
- the line of action should be visible even in small sprites
- contact and apex poses need larger spacing than transitional frames

## Timing Rules

Use frame timing as a design tool, not just a mechanical setting.

- hold longer on anticipation when clarity matters
- move quickly through the travel segment when force matters
- hold impact or apex briefly if the move should feel heavy or heroic
- shorten holds for nervous, agile, or evasive motion

## Secondary Motion Rules

JumpClip should support secondary motion but keep it subordinate to the action read.

Eligible secondary systems:

- cloth tails
- hair masses
- capes and hems
- hanging charms
- tails, crests, antennae, wing tips
- carried props

Secondary motion should:

- lag behind the main mass
- overshoot slightly after reversals
- settle after the primary body settles
- never obscure the hit frame or contact frame

## Character Rig Standard

JumpClip should assume an abstract rig vocabulary even when the renderer is procedural.

Primary control zones:

- root
- pelvis
- chest
- neck
- head
- shoulder left and right
- elbow left and right
- wrist left and right
- hip left and right
- knee left and right
- ankle left and right
- prop attachment slots

Optional zones:

- cloak root
- tail root and tip
- hair front and back masses
- antenna or ear tips
- shoulder ornaments

## Equipment And Pose Compatibility

Animation must respect carried form.

Rules:

- one-handed and two-handed stances should be separate templates
- shield, lantern, staff, blade, firearm, and heavy tool reads should each own different idle and anticipation logic
- large back attachments must not erase torso twist readability
- cloak and skirt shapes should be authored to reveal step cadence, not hide it

## Key-Pose Tags For JumpClip

Recommended internal tags:

- `grounded_load`
- `airborne_extension`
- `impact_contact`
- `recoil_settle`
- `guard_return`
- `ritual_hold`
- `look_focus`
- `brace_left`
- `brace_right`
- `twist_release`
- `landing_catch`
- `stagger_back`

These tags are useful for future tooling, review UIs, or learning-model biasing.

## Motion Override Mapping

### `motion_silhouette_bias`

Increase when the move must read more iconically at small size.

### `motion_squash_stretch`

Increase for agile, comic, or elastic motion. Keep lower for heavy or realistic attacks.

### `motion_impact`

Increase to widen anticipation-to-hit contrast and strengthen contact readability.

### `motion_lift`

Increase for jump arcs, heroic attacks, and stylized recovery. Keep lower for rooted or oppressive motion.

## Pose Review Checklist

Before approving an animation strip, confirm:

- the intent is readable from key poses alone
- the action path is visible in silhouette
- the strongest frame is not hidden by costume clutter
- the contact or apex frame is not under-spaced
- secondary motion supports the move instead of competing with it
- the motion family matches the character's role

## Bottom Line

JumpClip should generate animations as sequences of decisions, not just frame counts. Strong key poses, timing contrast, and clean action lines matter more than frame abundance.