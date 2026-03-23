from football_predictor.live_scene import scene_from_report, synthesize_live_match_scene
from football_predictor.sport_rules import get_action_catalog, get_sport_ruleset


def _simulation_result(sport: str) -> dict:
    return {
        "sport": sport,
        "home_team": "Home",
        "away_team": "Away",
        "event_trajectories": [
            {
                "team": "home",
                "minute": 12.0,
                "trajectory": [
                    {
                        "t": 0.0,
                        "x": 52.0 if sport == "football" else (14.0 if sport == "baseball" else 70.0),
                        "y": 34.0 if sport == "football" else (14.0 if sport == "baseball" else 24.0),
                        "z": 0.2 if sport != "basketball" else 2.0,
                    },
                    {
                        "t": 0.8,
                        "x": 105.0 if sport == "football" else (85.0 if sport == "baseball" else 88.0),
                        "y": 34.0 if sport == "football" else (82.0 if sport == "baseball" else 25.0),
                        "z": 1.1 if sport != "basketball" else 3.05,
                    },
                ],
            }
        ],
    }


def _out_of_bounds_simulation_result() -> dict:
    return {
        "sport": "football",
        "home_team": "Home",
        "away_team": "Away",
        "event_trajectories": [
            {
                "team": "home",
                "minute": 22.0,
                "trajectory": [
                    {"t": 0.0, "x": 101.0, "y": 66.0, "z": 0.4},
                    {"t": 0.5, "x": 109.0, "y": 71.0, "z": 0.9},
                ],
            }
        ],
    }


def test_synthesize_live_match_scene_builds_full_team_frames_for_football():
    scene = synthesize_live_match_scene(_simulation_result("football"), match_seconds=24.0, fps=5)
    assert scene["sport"] == "football"
    assert len(scene["frames"]) == 121
    first = scene["frames"][0]
    last = scene["frames"][-1]
    assert len(first["home_players"]) == 11
    assert len(first["away_players"]) == 11
    assert first["home_score"] == 0
    assert last["home_score"] == 1
    assert 0.15 <= last["crowd_intensity"] <= 1.0
    assert scene["physics"]["max_speed"] > 0.0
    assert first["home_players"][0]["action"] in set(get_action_catalog("football")) | {"set"}
    assert first["home_players"][0]["decision_state"] in scene["ruleset"]["decision_states"]
    assert first["home_players"][0]["mistake_state"] in set(scene["ruleset"]["mistake_states"]) | {"stable"}
    assert first["home_players"][0]["speed"] >= 0.0
    assert first["ball_speed"] >= 0.0
    assert "attention_focus" in first
    assert "spectator_prompt" in first


def test_scene_from_report_supports_basketball_player_counts():
    report = {"simulations": [_simulation_result("basketball")]}
    scene = scene_from_report(report, fps=4)
    frame = scene["frames"][10]
    assert scene["sport"] == "basketball"
    assert len(frame["home_players"]) == 5
    assert len(frame["away_players"]) == 5
    assert frame["possession"] in {"home", "away"}
    assert any(player["action"] in set(get_action_catalog("basketball")) | {"set"} for player in frame["home_players"] + frame["away_players"])


def test_scene_from_report_supports_baseball_player_counts():
    report = {"simulations": [_simulation_result("baseball")]}
    scene = scene_from_report(report, fps=4)
    frame = scene["frames"][10]
    assert scene["sport"] == "baseball"
    assert len(frame["home_players"]) == 9
    assert len(frame["away_players"]) == 9
    assert frame["camera_target"][2] >= 1.0
    assert frame["phase"] in set(get_sport_ruleset("baseball")["phase_states"])


def test_live_scene_recovers_ball_at_boundaries():
    scene = synthesize_live_match_scene(_out_of_bounds_simulation_result(), match_seconds=12.0, fps=6)
    recovered_frames = [frame for frame in scene["frames"] if frame["phase"] == "out_of_bounds_recovery"]
    assert recovered_frames
    for frame in recovered_frames:
        assert 0.0 <= frame["ball"][0] <= scene["surface"]["length"]
        assert 0.0 <= frame["ball"][1] <= scene["surface"]["width"]
    last = scene["frames"][-1]
    edge_players = [player for player in last["home_players"] + last["away_players"] if player["x"] >= scene["surface"]["length"] - 1.0 or player["y"] >= scene["surface"]["width"] - 1.0]
    assert edge_players


def test_scene_reports_behavior_state_fields():
    scene = synthesize_live_match_scene(_simulation_result("basketball"), match_seconds=14.0, fps=5)
    frame = scene["frames"][8]
    player = frame["home_players"][0]
    assert player["behavior_state"] == player["action"]
    assert player["decision_state"] in scene["ruleset"]["decision_states"]
    assert player["mistake_state"] in set(scene["ruleset"]["mistake_states"]) | {"stable"}
    assert frame["pressure_window"] in {"wide_window", "standard_window", "tight_window"}
    assert frame["focus_radius"] > 0.0