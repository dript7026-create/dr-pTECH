from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

from prototype_gameplay_flow import GameplayPrototypeController
from xenobloods_adaptive_director import CombatTelemetry, build_chapter_plan
from xenobloods_systems import LifeForm, Plane, create_starting_player


DEMO_THRESHOLDS = [
    'landborne_entry',
    'ether_recall',
    'gourd_incubation',
    'landborne_reborn',
    'boss_intro',
    'boss_clash',
    'boss_defeat',
]

PLAYER_LAYOUT = {
    'landborne': {'position': [-9.8, 1.1, 8.6], 'tint': [214, 122, 102]},
    'gourd_infant': {'position': [0.0, 1.0, 7.8], 'tint': [210, 176, 112]},
    'etheric_current': {'position': [9.8, 1.2, 8.6], 'tint': [126, 176, 255]},
}

ENCOUNTER_LAYOUT = {
    'scarab_child_acolyte': {'position': [-6.4, 1.1, 23.4], 'tint': [178, 134, 116]},
    'lattice_ward': {'position': [6.6, 1.2, 23.9], 'tint': [188, 204, 238]},
    'lahgroid_hierophant': {'position': [0.0, 1.9, 29.4], 'tint': [214, 152, 120]},
}


def _serialize_player(player) -> dict:
    return {
        'name': player.name,
        'plane': player.plane.value,
        'life_form': player.life_form.value,
        'alignment': player.alignment.value,
        'blood_current': player.blood.current,
        'blood_maximum': player.blood.maximum,
        'health': player.health,
        'stamina': player.stamina,
        'mental_acuity': player.mental_acuity,
        'rupture_progress': player.rupture_progress,
        'gourd_capacity': player.gourd.capacity,
        'gourd_stored_blood': player.gourd.stored_blood,
        'gourd_shell_integrity': player.gourd.shell_integrity,
        'gourd_infant_charge': player.gourd.infant_charge,
        'spilled_blood_pool': player.spilled_blood_pool,
    }


def _serialize_battle_state(controller: GameplayPrototypeController) -> dict | None:
    if controller.battle_state is None:
        return None
    return {
        'enemy_id': controller.battle_state.enemy_id,
        'enemy_health': controller.battle_state.enemy_health,
        'player_health': controller.battle_state.player_health,
        'beat_index': controller.battle_state.beat_index,
        'telegraphs': list(controller.battle_state.telegraphs),
        'last_resolution': controller.battle_state.last_resolution,
    }


def _seed_object_state(bindings: dict) -> dict:
    object_state = {}
    for binding_id, binding in bindings.items():
        role = str(binding.get('kind', 'world-prop'))
        object_state[binding_id] = {
            'object_id': binding.get('object_id'),
            'kind': role,
            'visited': False,
            'activated': False,
        }
        if role == 'village-house':
            object_state[binding_id]['blood_cache'] = 12.0
        if role == 'shrine-marker':
            object_state[binding_id]['plane_target'] = binding.get('plane_target', 'land')
    return object_state


def _set_binding_flags(objects: dict, *binding_ids: str, visited: bool | None = None, activated: bool | None = None, **extra: object) -> None:
    for binding_id in binding_ids:
        if binding_id not in objects:
            continue
        if visited is not None:
            objects[binding_id]['visited'] = visited
        if activated is not None:
            objects[binding_id]['activated'] = activated
        objects[binding_id].update(extra)


class XenoBloodsDoEngineBridge:
    def __init__(self, package_manifest: dict) -> None:
        self.package_manifest = package_manifest

    @property
    def bindings(self) -> dict:
        payload = self.package_manifest if isinstance(self.package_manifest, dict) else {}
        return payload.get('gameplay_bindings', {}) if isinstance(payload.get('gameplay_bindings', {}), dict) else {}

    def _telemetry(self) -> CombatTelemetry:
        return CombatTelemetry(
            parry_success_rate=0.42,
            late_dodge_rate=0.28,
            overcommit_rate=0.19,
            heal_panic_rate=0.16,
            crowd_separation_rate=0.54,
            ranged_interrupt_rate=0.36,
            boss_retry_count=1,
            dominant_style_tags=['parry_hungry'],
        )

    def _compose_state(
        self,
        *,
        player,
        objects: dict,
        telemetry: CombatTelemetry,
        checkpoint_id: str,
        label: str,
        current_biome: str,
        current_actor_id: str | None,
        mode: str,
        status_text: str,
        threshold_index: int,
        activated_shrines: list[str],
        visited_houses: list[str],
        sewer_unlocked: bool,
        boss_stage: str = 'unseen',
        boss_health: float | None = None,
        battle_state: dict | None = None,
        boss_defeated: bool = False,
    ) -> dict:
        return {
            'player': _serialize_player(player),
            'world': {
                'current_biome': current_biome,
                'sewer_unlocked': sewer_unlocked,
                'activated_shrines': list(activated_shrines),
                'visited_houses': list(visited_houses),
                'boss_defeated': boss_defeated,
            },
            'objects': deepcopy(objects),
            'encounter_plan': [asdict(packet) for packet in build_chapter_plan(telemetry)],
            'combat_telemetry': asdict(telemetry),
            'demo': {
                'checkpoint_id': checkpoint_id,
                'label': label,
                'mode': mode,
                'current_actor_id': current_actor_id,
                'status_text': status_text,
                'boss_stage': boss_stage,
                'boss_health': boss_health,
                'boss_max_health': 120.0,
                'threshold_index': threshold_index,
                'available_checkpoints': list(DEMO_THRESHOLDS),
                'battle_state': deepcopy(battle_state),
            },
        }

    def build_demo_states(self) -> list[dict[str, object]]:
        bindings = self.bindings
        telemetry = self._telemetry()
        stages: list[dict[str, object]] = []

        land_player = create_starting_player('Shellfarer')
        land_controller = GameplayPrototypeController(land_player)
        land_controller.enter_land_navigation('veinmarket')
        land_objects = _seed_object_state(bindings)
        _set_binding_flags(land_objects, 'soul_shrine_03', activated=True)
        _set_binding_flags(land_objects, 'village_house_01', visited=True)
        stages.append(
            {
                'save_name': 'landborne_entry',
                'label': 'Landborne Entry',
                'gameplay_state': self._compose_state(
                    player=land_player,
                    objects=land_objects,
                    telemetry=telemetry,
                    checkpoint_id='landborne_entry',
                    label='Landborne Entry',
                    current_biome='pikerel_village',
                    current_actor_id='scarab_child_acolyte',
                    mode=land_controller.mode.value,
                    status_text=land_controller.status_text,
                    threshold_index=0,
                    activated_shrines=['soul_shrine_03'],
                    visited_houses=['village_house_01'],
                    sewer_unlocked=False,
                ),
            }
        )

        ether_player = create_starting_player('Shellfarer')
        ether_player.die()
        ether_controller = GameplayPrototypeController(ether_player)
        ether_objects = _seed_object_state(bindings)
        _set_binding_flags(ether_objects, 'soul_shrine_01', activated=True)
        stages.append(
            {
                'save_name': 'ether_recall',
                'label': 'Ether Recall',
                'gameplay_state': self._compose_state(
                    player=ether_player,
                    objects=ether_objects,
                    telemetry=telemetry,
                    checkpoint_id='ether_recall',
                    label='Ether Recall',
                    current_biome='shrine_ether',
                    current_actor_id=None,
                    mode='ether_drift',
                    status_text='Ishtasha has shed into ether and can only route through shrines and soul current.',
                    threshold_index=1,
                    activated_shrines=['soul_shrine_01'],
                    visited_houses=[],
                    sewer_unlocked=False,
                ),
            }
        )

        gourd_player = create_starting_player('Shellfarer')
        gourd_player.die()
        gourd_player.descend_into_land()
        gourd_player.struggle_in_gourd(58.0)
        gourd_controller = GameplayPrototypeController(gourd_player)
        gourd_objects = _seed_object_state(bindings)
        _set_binding_flags(gourd_objects, 'soul_shrine_02', activated=True)
        stages.append(
            {
                'save_name': 'gourd_incubation',
                'label': 'Gourd Incubation',
                'gameplay_state': self._compose_state(
                    player=gourd_player,
                    objects=gourd_objects,
                    telemetry=telemetry,
                    checkpoint_id='gourd_incubation',
                    label='Gourd Incubation',
                    current_biome='birth_nest',
                    current_actor_id=None,
                    mode='gourd_incubation',
                    status_text='The amniotic gourd is incubating. Rupture progress and shell pressure now govern rebirth.',
                    threshold_index=2,
                    activated_shrines=['soul_shrine_02'],
                    visited_houses=[],
                    sewer_unlocked=False,
                ),
            }
        )

        reborn_player = create_starting_player('Shellfarer')
        reborn_player.die()
        reborn_player.descend_into_land()
        reborn_player.struggle_in_gourd(100.0)
        reborn_player.hatch_from_gourd()
        reborn_controller = GameplayPrototypeController(reborn_player)
        reborn_controller.enter_land_navigation('ossuary_rise')
        reborn_objects = _seed_object_state(bindings)
        _set_binding_flags(reborn_objects, 'soul_shrine_01', 'soul_shrine_02', 'soul_shrine_03', activated=True)
        _set_binding_flags(reborn_objects, 'village_house_01', 'village_house_02', 'village_house_03', visited=True)
        stages.append(
            {
                'save_name': 'landborne_reborn',
                'label': 'Landborne Reborn',
                'gameplay_state': self._compose_state(
                    player=reborn_player,
                    objects=reborn_objects,
                    telemetry=telemetry,
                    checkpoint_id='landborne_reborn',
                    label='Landborne Reborn',
                    current_biome='ossuary_rise',
                    current_actor_id='lattice_ward',
                    mode=reborn_controller.mode.value,
                    status_text='The vessel has hatched again. Ishtasha is ready to push deeper into Land and face harder reads.',
                    threshold_index=3,
                    activated_shrines=['soul_shrine_01', 'soul_shrine_02', 'soul_shrine_03'],
                    visited_houses=['village_house_01', 'village_house_02', 'village_house_03'],
                    sewer_unlocked=False,
                ),
            }
        )

        boss_intro_player = create_starting_player('Shellfarer')
        boss_intro_player.die()
        boss_intro_player.descend_into_land()
        boss_intro_player.struggle_in_gourd(100.0)
        boss_intro_player.hatch_from_gourd()
        boss_intro_controller = GameplayPrototypeController(boss_intro_player)
        boss_intro_controller.enter_land_navigation('boss_gate')
        boss_intro_controller.begin_boss_sequence()
        boss_intro_objects = _seed_object_state(bindings)
        _set_binding_flags(boss_intro_objects, 'soul_shrine_01', 'soul_shrine_02', 'soul_shrine_03', activated=True)
        _set_binding_flags(
            boss_intro_objects,
            'village_house_01',
            'village_house_02',
            'village_house_03',
            'village_house_04',
            'village_house_05',
            'village_house_06',
            visited=True,
        )
        _set_binding_flags(boss_intro_objects, 'sewer_preview_gate', activated=True)
        stages.append(
            {
                'save_name': 'boss_intro',
                'label': 'Boss Intro',
                'gameplay_state': self._compose_state(
                    player=boss_intro_player,
                    objects=boss_intro_objects,
                    telemetry=telemetry,
                    checkpoint_id='boss_intro',
                    label='Boss Intro',
                    current_biome='boss_gate',
                    current_actor_id='lahgroid_hierophant',
                    mode=boss_intro_controller.mode.value,
                    status_text=boss_intro_controller.status_text,
                    threshold_index=4,
                    activated_shrines=['soul_shrine_01', 'soul_shrine_02', 'soul_shrine_03'],
                    visited_houses=[
                        'village_house_01',
                        'village_house_02',
                        'village_house_03',
                        'village_house_04',
                        'village_house_05',
                        'village_house_06',
                    ],
                    sewer_unlocked=True,
                    boss_stage='intro',
                    boss_health=boss_intro_controller.battle_state.enemy_health if boss_intro_controller.battle_state else 120.0,
                    battle_state=_serialize_battle_state(boss_intro_controller),
                ),
            }
        )

        boss_clash_player = create_starting_player('Shellfarer')
        boss_clash_player.die()
        boss_clash_player.descend_into_land()
        boss_clash_player.struggle_in_gourd(100.0)
        boss_clash_player.hatch_from_gourd()
        boss_clash_controller = GameplayPrototypeController(boss_clash_player)
        boss_clash_controller.enter_land_navigation('boss_gate')
        boss_clash_controller.begin_boss_sequence()
        boss_clash_controller.resolve_boss_exchange('dodge', 0.5, 'background', ranged=True)
        boss_clash_controller.resolve_boss_exchange('parry', 0.5, 'midground', ranged=False)
        boss_clash_objects = deepcopy(boss_intro_objects)
        stages.append(
            {
                'save_name': 'boss_clash',
                'label': 'Boss Clash',
                'gameplay_state': self._compose_state(
                    player=boss_clash_player,
                    objects=boss_clash_objects,
                    telemetry=telemetry,
                    checkpoint_id='boss_clash',
                    label='Boss Clash',
                    current_biome='boss_gate',
                    current_actor_id='lahgroid_hierophant',
                    mode=boss_clash_controller.mode.value,
                    status_text=boss_clash_controller.status_text,
                    threshold_index=5,
                    activated_shrines=['soul_shrine_01', 'soul_shrine_02', 'soul_shrine_03'],
                    visited_houses=[
                        'village_house_01',
                        'village_house_02',
                        'village_house_03',
                        'village_house_04',
                        'village_house_05',
                        'village_house_06',
                    ],
                    sewer_unlocked=True,
                    boss_stage='clash',
                    boss_health=boss_clash_controller.battle_state.enemy_health if boss_clash_controller.battle_state else 0.0,
                    battle_state=_serialize_battle_state(boss_clash_controller),
                ),
            }
        )

        boss_defeat_player = create_starting_player('Shellfarer')
        boss_defeat_player.die()
        boss_defeat_player.descend_into_land()
        boss_defeat_player.struggle_in_gourd(100.0)
        boss_defeat_player.hatch_from_gourd()
        boss_defeat_controller = GameplayPrototypeController(boss_defeat_player)
        boss_defeat_controller.enter_land_navigation('boss_gate')
        boss_defeat_controller.begin_boss_sequence()
        while boss_defeat_controller.mode.value == 'boss_realtime' and boss_defeat_controller.battle_state is not None:
            expected_action, expected_lane = boss_defeat_controller.battle_state.telegraphs[
                boss_defeat_controller.battle_state.beat_index % len(boss_defeat_controller.battle_state.telegraphs)
            ]
            boss_defeat_controller.resolve_boss_exchange(expected_action, 0.5, expected_lane, ranged=expected_lane == 'background')
        boss_defeat_objects = deepcopy(boss_intro_objects)
        stages.append(
            {
                'save_name': 'boss_defeat',
                'label': 'Boss Defeat',
                'gameplay_state': self._compose_state(
                    player=boss_defeat_player,
                    objects=boss_defeat_objects,
                    telemetry=telemetry,
                    checkpoint_id='boss_defeat',
                    label='Boss Defeat',
                    current_biome='sunken_sanctum',
                    current_actor_id='lahgroid_hierophant',
                    mode=boss_defeat_controller.mode.value,
                    status_text=boss_defeat_controller.status_text,
                    threshold_index=6,
                    activated_shrines=['soul_shrine_01', 'soul_shrine_02', 'soul_shrine_03'],
                    visited_houses=[
                        'village_house_01',
                        'village_house_02',
                        'village_house_03',
                        'village_house_04',
                        'village_house_05',
                        'village_house_06',
                    ],
                    sewer_unlocked=True,
                    boss_stage='defeated',
                    boss_health=0.0,
                    battle_state=None,
                    boss_defeated=True,
                ),
            }
        )

        return stages

    def create_initial_state(self) -> dict:
        demo_states = self.build_demo_states()
        if demo_states:
            return deepcopy(demo_states[0]['gameplay_state'])
        player = create_starting_player('Shellfarer')
        return {
            'player': _serialize_player(player),
            'world': {'current_biome': 'pikerel_village', 'sewer_unlocked': False, 'activated_shrines': [], 'visited_houses': []},
            'objects': _seed_object_state(self.bindings),
            'encounter_plan': [],
            'combat_telemetry': {},
            'demo': {'checkpoint_id': 'bootstrap', 'label': 'Bootstrap', 'mode': 'land_navigation', 'current_actor_id': None, 'status_text': ''},
        }

    def build_runtime_overrides(self, gameplay_state: dict, bindings: dict) -> dict:
        player = gameplay_state.get('player', {}) if isinstance(gameplay_state, dict) else {}
        world = gameplay_state.get('world', {}) if isinstance(gameplay_state, dict) else {}
        objects = gameplay_state.get('objects', {}) if isinstance(gameplay_state, dict) else {}
        demo = gameplay_state.get('demo', {}) if isinstance(gameplay_state, dict) else {}
        blood_maximum = max(1.0, float(player.get('blood_maximum', 120.0)))
        blood_ratio = max(0.0, min(1.0, float(player.get('blood_current', 120.0)) / blood_maximum))
        visited_house_count = sum(1 for state in objects.values() if isinstance(state, dict) and state.get('kind') == 'village-house' and state.get('visited'))
        active_shrine_count = len(world.get('activated_shrines', [])) if isinstance(world.get('activated_shrines'), list) else 0
        total_houses = max(1, sum(1 for binding in bindings.values() if isinstance(binding, dict) and binding.get('kind') == 'village-house'))
        house_ratio = visited_house_count / total_houses
        sewer_unlocked = bool(world.get('sewer_unlocked', False))
        current_actor_id = str(demo.get('current_actor_id') or '')
        life_form = str(player.get('life_form', 'landborne'))
        boss_stage = str(demo.get('boss_stage', 'unseen'))
        boss_max = max(1.0, float(demo.get('boss_max_health', 120.0) or 120.0))
        boss_health = float(demo.get('boss_health', boss_max) or boss_max)
        boss_pressure = max(0.0, min(1.0, 1.0 - boss_health / boss_max)) if boss_stage != 'unseen' else 0.0
        threshold_index = int(demo.get('threshold_index', 0))
        threshold_index = max(0, min(len(DEMO_THRESHOLDS) - 1, threshold_index))
        return {
            'pressure_wave': round(0.18 + blood_ratio * 0.52 + boss_pressure * 0.2, 4),
            'relay_resonance': round(min(1.0, 0.1 + active_shrine_count * 0.24 + house_ratio * 0.22), 4),
            'ooze_surge': round(min(1.0, 0.16 + house_ratio * 0.48 + (0.2 if sewer_unlocked else 0.0)), 4),
            'fracture_pulse': round(min(1.0, float(player.get('rupture_progress', 0.0)) / 100.0), 4),
            'stall_decay': round(max(0.0, 1.0 - blood_ratio * 0.68), 4),
            'xenobloods_plane': str(player.get('plane', 'land')),
            'xenobloods_alignment': str(player.get('alignment', 'mortal')),
            'xenobloods_life_state': life_form,
            'xenobloods_life_state_index': round(threshold_index / max(1, len(DEMO_THRESHOLDS) - 1), 4),
            'life_state_landborne': 1.0 if life_form == LifeForm.LANDBORNE.value else 0.24,
            'life_state_gourd_infant': 1.0 if life_form == LifeForm.GOURD_INFANT.value else 0.24,
            'life_state_etheric_current': 1.0 if life_form == LifeForm.ETHERIC_CURRENT.value else 0.24,
            'encounter_focus_scarab': 1.0 if current_actor_id == 'scarab_child_acolyte' else 0.18,
            'encounter_focus_lattice': 1.0 if current_actor_id == 'lattice_ward' else 0.18,
            'boss_focus': 1.0 if boss_stage != 'unseen' else 0.24,
            'boss_pressure': round(boss_pressure, 4),
            'thresholds': list(DEMO_THRESHOLDS),
            'active_threshold_index': threshold_index,
            'active_threshold': DEMO_THRESHOLDS[threshold_index],
            'xenobloods_demo_checkpoint': str(demo.get('checkpoint_id', 'landborne_entry')),
        }

    def build_scene_state(self, gameplay_state: dict, bindings: dict) -> dict:
        player = gameplay_state.get('player', {}) if isinstance(gameplay_state, dict) else {}
        world = gameplay_state.get('world', {}) if isinstance(gameplay_state, dict) else {}
        demo = gameplay_state.get('demo', {}) if isinstance(gameplay_state, dict) else {}
        objects = gameplay_state.get('objects', {}) if isinstance(gameplay_state, dict) else {}
        active_life_form = str(player.get('life_form', LifeForm.LANDBORNE.value))
        active_actor = str(demo.get('current_actor_id') or '')
        boss_stage = str(demo.get('boss_stage', 'unseen'))
        mesh_updates: list[dict] = []
        billboard_updates: list[dict] = []

        activated_shrines = set(world.get('activated_shrines', [])) if isinstance(world.get('activated_shrines'), list) else set()
        visited_houses = set(world.get('visited_houses', [])) if isinstance(world.get('visited_houses'), list) else set()

        for binding_id, binding in bindings.items():
            if not isinstance(binding, dict):
                continue
            object_id = str(binding.get('object_id', ''))
            role = str(binding.get('kind', 'world-prop'))
            if role == 'village-house':
                is_visited = binding_id in visited_houses or bool(objects.get(binding_id, {}).get('visited'))
                mesh_updates.append(
                    {
                        'id': object_id,
                        'material': 'amber' if is_visited else 'stone',
                        'scale': 1.04 if is_visited else 1.0,
                        'scripts': [{'type': 'bob', 'amplitude': 0.05 if is_visited else 0.04, 'speed': 0.28}],
                    }
                )
            elif role == 'shrine-marker':
                is_active = binding_id in activated_shrines or bool(objects.get(binding_id, {}).get('activated'))
                mesh_updates.append(
                    {
                        'id': object_id,
                        'material': 'amber' if is_active else 'bone',
                        'scale': 1.08 if is_active else 1.0,
                        'scripts': [{'type': 'pulse', 'amplitude': 0.08 if is_active else 0.03, 'speed': 0.85 if is_active else 0.45}],
                    }
                )
            elif role == 'future-biome-preview':
                is_unlocked = bool(world.get('sewer_unlocked', False))
                mesh_updates.append(
                    {
                        'id': object_id,
                        'material': 'jade' if is_unlocked else 'shadow',
                        'scale': 0.96 if is_unlocked else 0.85,
                        'scripts': [{'type': 'threshold_gate', 'threshold': 'boss_intro', 'y_amplitude': 0.18, 'scale_amplitude': 0.12}],
                    }
                )
            elif role == 'player-life-state':
                life_form = str(binding.get('life_form', 'landborne'))
                layout = PLAYER_LAYOUT.get(life_form, PLAYER_LAYOUT['landborne'])
                active = life_form == active_life_form
                billboard_updates.append(
                    {
                        'id': object_id,
                        'position': layout['position'],
                        'width': 432 if active else 248,
                        'height': 432 if active else 248,
                        'label': f"{binding.get('label')}" if active else str(binding.get('label')),
                        'tint': layout['tint'],
                        'scripts': [
                            {'type': 'channel_follow', 'channel': f'life_state_{life_form}', 'y_amplitude': 0.16, 'scale_amplitude': 0.22, 'speed': 0.72},
                            {'type': 'pulse', 'amplitude': 0.08 if active else 0.03, 'speed': 0.82 if active else 0.38},
                        ],
                    }
                )
            elif role == 'encounter-preview':
                actor_id = str(binding.get('actor_id', ''))
                layout = ENCOUNTER_LAYOUT.get(actor_id, ENCOUNTER_LAYOUT['scarab_child_acolyte'])
                active = actor_id == active_actor and boss_stage == 'unseen'
                billboard_updates.append(
                    {
                        'id': object_id,
                        'position': layout['position'],
                        'width': 324 if active else 224,
                        'height': 300 if active else 210,
                        'tint': layout['tint'],
                        'scripts': [
                            {'type': 'channel_follow', 'channel': 'encounter_focus_scarab' if actor_id == 'scarab_child_acolyte' else 'encounter_focus_lattice', 'y_amplitude': 0.14, 'scale_amplitude': 0.18, 'speed': 0.66},
                        ],
                    }
                )
            elif role == 'boss-preview':
                layout = ENCOUNTER_LAYOUT['lahgroid_hierophant']
                active = boss_stage != 'unseen'
                billboard_updates.append(
                    {
                        'id': object_id,
                        'position': layout['position'],
                        'width': 560 if active else 252,
                        'height': 520 if active else 236,
                        'label': 'Lahgroid Hierophant' if boss_stage != 'defeated' else 'Lahgroid Broken',
                        'tint': [226, 178, 122] if boss_stage != 'defeated' else [154, 188, 214],
                        'scripts': [
                            {'type': 'channel_follow', 'channel': 'boss_focus', 'y_amplitude': 0.18, 'scale_amplitude': 0.2, 'speed': 0.6},
                            {'type': 'threshold_gate', 'threshold': 'boss_intro', 'y_amplitude': 0.22, 'scale_amplitude': 0.14, 'speed': 0.74},
                            {'type': 'accent_burst', 'channel': 'boss_pressure', 'scale_amplitude': 0.18, 'y_amplitude': 0.2, 'curve': 6.0, 'speed': 1.1},
                        ],
                    }
                )

        return {'mesh_instances': mesh_updates, 'billboards': billboard_updates}


def create_bridge(package_manifest: dict) -> XenoBloodsDoEngineBridge:
    return XenoBloodsDoEngineBridge(package_manifest)