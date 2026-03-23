from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

from .sports import normalize_sport


COMMON_IMPAIRMENTS = [
    "fatigue_drag",
    "confusion",
    "vision_acuity_disruption",
    "reaction_delay",
    "spatial_disorientation",
    "coordination_drop",
    "balance_loss",
    "composure_dip",
    "crowd_disruption",
    "decision_noise",
    "hesitation",
]

COMMON_DECISION_STATES = [
    "scan",
    "commit",
    "anticipate",
    "defer",
    "hesitate",
    "recover",
]

SPORT_ROLE_SEQUENCES: Dict[str, List[str]] = {
    "football": ["GK", "LB", "CB", "CB", "RB", "DM", "CM", "AM", "LW", "ST", "RW"],
    "baseball": ["P", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"],
    "basketball": ["PG", "SG", "SF", "PF", "C"],
}

SPORT_RULESETS: Dict[str, Dict[str, object]] = {
    "football": {
        "role_sequence": SPORT_ROLE_SEQUENCES["football"],
        "phase_states": [
            "kickoff_restart",
            "settled_possession",
            "counterattack",
            "free_kick_restart",
            "corner_restart",
            "throw_in_restart",
            "goal_kick_restart",
            "penalty_sequence",
            "offside_reset",
            "foul_advantage",
            "keeper_distribution",
            "out_of_bounds_recovery",
            "finishing_sequence",
        ],
        "control_actions": ["receive", "carry", "shield", "short_pass", "switch_pass", "through_ball", "cross"],
        "support_actions": ["scan", "support_run", "overlap", "underlap", "drop_cover", "hold_line", "recover_shape"],
        "defensive_actions": ["press", "jockey", "mark", "block_lane", "intercept", "clear", "guard_goal"],
        "scoring_actions": ["shoot", "header", "release"],
        "recovery_actions": ["recover", "regather", "retreat", "reset_shape"],
        "mistake_states": ["heavy_touch", "misread_pass", "late_track", "hesitation", "stumble", "vision_blur"],
        "impairment_states": COMMON_IMPAIRMENTS,
        "decision_states": COMMON_DECISION_STATES,
    },
    "baseball": {
        "role_sequence": SPORT_ROLE_SEQUENCES["baseball"],
        "phase_states": [
            "pitch_setup",
            "live_pitch",
            "contact_play",
            "foul_ball_reset",
            "force_play",
            "tag_play",
            "dead_ball_reset",
            "inning_change",
            "outfield_retrieval",
            "base_running_pressure",
            "scoring_contact",
        ],
        "control_actions": ["set_pitch", "receive_pitch", "work_count", "field_transfer", "relay_throw", "lead_off"],
        "support_actions": ["back_up_throw", "cover_base", "hold_runner", "shade_gap", "track_flight", "base_shuffle"],
        "defensive_actions": ["frame_pitch", "tag_runner", "force_out", "cut_off_lane", "stay_home", "chase_ball"],
        "scoring_actions": ["swing_contact", "drive_gap", "sacrifice_fly", "steal_break"],
        "recovery_actions": ["regather", "scramble", "relay_recover", "dead_ball_reset"],
        "mistake_states": ["wild_throw", "late_break", "misjudge_flight", "hesitation", "overrun_ball", "blurred_read"],
        "impairment_states": COMMON_IMPAIRMENTS,
        "decision_states": COMMON_DECISION_STATES,
    },
    "basketball": {
        "role_sequence": SPORT_ROLE_SEQUENCES["basketball"],
        "phase_states": [
            "inbound_restart",
            "half_court_set",
            "transition_push",
            "dribble_drive",
            "catch_and_shoot_window",
            "closeout_pressure",
            "rebound_scramble",
            "turnover_recovery",
            "shot_clock_pressure",
            "free_throw_sequence",
            "finishing_sequence",
        ],
        "control_actions": ["receive", "dribble_probe", "swing_pass", "post_entry", "jab_step", "screen_reject"],
        "support_actions": ["relocate", "screen", "cut", "space_floor", "crash_glass", "tag_roller"],
        "defensive_actions": ["press", "contain_drive", "close_out", "switch", "box_out", "guard_rim"],
        "scoring_actions": ["pull_up", "catch_and_shoot", "layup", "dunk", "release"],
        "recovery_actions": ["recover", "scramble", "reset", "retreat"],
        "mistake_states": ["loose_handle", "late_rotation", "rushed_release", "hesitation", "stumble", "blind_side_loss"],
        "impairment_states": COMMON_IMPAIRMENTS,
        "decision_states": COMMON_DECISION_STATES,
    },
}


def get_sport_ruleset(sport: str | None) -> Dict[str, object]:
    return deepcopy(SPORT_RULESETS[normalize_sport(sport)])


def get_role_sequence(sport: str | None) -> List[str]:
    return list(get_sport_ruleset(sport)["role_sequence"])


def get_action_catalog(sport: str | None) -> List[str]:
    ruleset = get_sport_ruleset(sport)
    seen = []
    for key in ["control_actions", "support_actions", "defensive_actions", "scoring_actions", "recovery_actions", "mistake_states"]:
        for value in ruleset[key]:
            if value not in seen:
                seen.append(value)
    return seen