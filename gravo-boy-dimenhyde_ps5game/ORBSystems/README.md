# ORBSystems

Purpose:
This directory is the parent hierarchy for the three ORBEngine gameplay/rendering ownership modules used by Gravo.

Modules:
- `ORBdimensionView/` owns pseudo-3D depth translation, visual plane interpretation, anchor logic, and screen-space presentation rules.
- `ORBKinetics/` owns movement-space collision, hit detection, hurtbox/hitbox interpretation, traversal contact rules, and responsive gameplay-space interaction.
- `ORBGlue/` binds authored art/data into runtime gameplay state, including shrine logic, MindSphereRivalary state exposure, equipment sockets, and presentation-to-system attachment.

Rule:
Every future Gravo asset integration task should identify which ORBSystem owns each authored signal before wiring it into runtime code.