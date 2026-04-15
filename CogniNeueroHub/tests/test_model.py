from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from cognineuerohub.model import Directive, animation_library_payload, bootstrap_state, dataset_payload, generate_student_lesson_note, lesson_library_payload, registry_payload, score_lesson_response, step_state


def test_bootstrap_counts_match_request():
    state = bootstrap_state(seed=5, agent_count=10, habitat_count=3)
    assert len(state.agents) == 10
    assert len(state.habitats) == 3
    assert state.tick == 0


def test_step_advances_tick_and_keeps_metrics_bounded():
    state = bootstrap_state(seed=7, agent_count=12, habitat_count=4)
    directive = Directive(curiosity_bias=0.8, equity_bias=0.75, challenge_bias=0.6, reflection_bias=0.85)
    step_state(state, steps=5, directive=directive)

    assert state.tick == 5
    assert 0.0 <= state.hub_consensus <= 1.0
    assert 0.0 <= state.mean_knowledge <= 1.0
    assert 0.0 <= state.mean_reflection <= 1.0
    assert 0.0 <= state.mean_coherence <= 1.0
    assert 0.0 <= state.friction <= 1.0


def test_registry_contains_hub_consensus_equation():
    payload = registry_payload()
    keys = {entry["key"] for entry in payload["equations"]}
    assert "hub_consensus" in keys


def test_default_bootstrap_loads_canonical_dataset():
    state = bootstrap_state()
    meta = dataset_payload()

    assert state.dataset_id == "artisapiens-seed-v1"
    assert meta["agent_count"] == len(state.agents)
    assert meta["habitat_count"] == len(state.habitats)


def test_lesson_library_contains_medieval_bavaria_pack():
    payload = lesson_library_payload()

    assert len(payload["lessons"]) >= 2
    assert payload["lessons"][0]["region"] == "Bavaria"
    assert payload["lessons"][0]["key_figures"][2] == "Otto of Wittelsbach"
    assert payload["lessons"][0]["depth"]["activity_count"] >= 3
    assert payload["lessons"][0]["phases"][0]["title"] == "Orient the map"
    assert payload["lessons"][0]["response_rubric"][1]["key"] == "evidence"
    assert payload["lessons"][0]["activities"][2]["type"] == "evidence_select"
    assert payload["lessons"][0]["animation_ids"] == ["teddy-bear-scribe", "fawn-route-guide"]
    assert payload["lessons"][0]["activities"][3]["type"] == "custom_game"
    assert payload["lessons"][0]["activities"][3]["config"]["game_type"] == "sequence_builder"


def test_animation_library_contains_local_teddy_and_fawn_assets():
    payload = animation_library_payload()

    assert payload["library_id"] == "lesson-animation-library-v1"
    assert len(payload["animations"]) >= 3
    assert payload["animations"][0]["asset_path"].startswith("/lesson-animations/")
    assert {item["animation_id"] for item in payload["animations"]} >= {"teddy-bear-scribe", "fawn-route-guide"}


def test_response_scoring_rewards_keyword_coverage():
    lesson = lesson_library_payload()["lessons"][0]
    state = bootstrap_state(seed=19, agent_count=12, habitat_count=4, lesson=lesson)
    analysis = score_lesson_response(
        state,
        "Bavaria stayed within the Holy Roman Empire while monastery networks, trade, and the Wittelsbach rise changed politics after investiture conflict.",
    )

    assert analysis.keyword_hits >= 4
    assert analysis.score > 0.5
    assert len(analysis.dimension_scores) == len(lesson["response_rubric"])
    assert any(dimension["key"] == "evidence" for dimension in analysis.dimension_scores)
    assert analysis.feedback


def test_course_profiles_generate_personalized_student_note():
    lesson = lesson_library_payload()["lessons"][0]
    course = {
        "title": "Bavaria Seminar Spring",
        "educator_name": "Dr. Rowan",
        "god_profile": {
            "conductor_name": "GodAI Seminar Voice",
            "tone": "steady mercy",
            "mercy_bias": 0.82,
            "challenge_bias": 0.6,
            "wonder_bias": 0.86,
        },
        "politeness_protocol": {
            "greeting_template": "Good morning",
            "affirmation_template": "Thank you for your patient attention",
            "closing_template": "Proceed with steady care",
            "redirection_template": "Let us return to the main evidence line",
        },
        "pace_profile": {
            "auto_pace_enabled": True,
            "manual_pace_bias": 0.44,
            "manual_clarity_bias": 0.82,
            "ai_authority": 0.74,
            "target_page_minutes": 5.0,
            "target_puzzle_seconds": 70.0,
            "live_metrics": {
                "page_minutes": 7.5,
                "average_puzzle_seconds": 115.0,
                "last_puzzle_seconds": 128.0,
                "active_activity_seconds": 39.0,
                "solved_activity_count": 2,
            },
        },
        "students": [
            {
                "student_id": "ada-l",
                "display_name": "Ada L.",
                "archetype": "careful synthesizer",
                "strengths": ["pattern recognition"],
                "support_needs": ["clear sequencing"],
                "interests": ["maps"],
                "preferred_modalities": ["discussion"],
                "egosphere": {
                    "trust": 0.66,
                    "fear": 0.34,
                    "adaptability": 0.72,
                    "reciprocity": 0.61,
                    "resonance": 0.83,
                    "dominance": 0.24,
                },
                "speech": {"voice_name": "Ada Voice", "voice_hint": "calm", "rate": 0.95, "pitch": 1.05, "volume": 1.0},
            }
        ],
    }
    state = bootstrap_state(seed=19, agent_count=12, habitat_count=4, lesson=lesson, course=course)

    note = generate_student_lesson_note(state, "ada-l")

    assert note.student_id == "ada-l"
    assert "Ada L." in note.specialized_note
    assert note.greeting.startswith("Good morning")
    assert note.closing.startswith("Proceed with steady care")
    assert note.guidance["conductor_name"] == "GodAI Seminar Voice"
    assert note.lesson_flow["compensation_mode"]
    assert note.lesson_flow["final_pace_label"] in {"slow and clear", "measured", "brisk"}
    assert note.speech["voice_hint"] == "calm"
    assert note.speech["voice_name"] == "Ada Voice"
    assert state.course.students[0].lesson_history
    assert note.focus_objective


def test_lesson_flow_detects_visual_obscurity_and_compensation():
    lesson = lesson_library_payload()["lessons"][0]
    course = {
        "pace_profile": {
            "auto_pace_enabled": True,
            "manual_pace_bias": 0.42,
            "manual_clarity_bias": 0.78,
            "ai_authority": 0.84,
            "target_page_minutes": 5.0,
            "target_puzzle_seconds": 70.0,
            "live_metrics": {
                "page_minutes": 8.6,
                "average_puzzle_seconds": 132.0,
                "last_puzzle_seconds": 141.0,
                "active_activity_seconds": 44.0,
                "solved_activity_count": 2,
            },
        }
    }
    state = bootstrap_state(seed=31, agent_count=12, habitat_count=4, lesson=lesson, course=course)
    directive = Directive(curiosity_bias=0.93, equity_bias=0.42, challenge_bias=0.96, reflection_bias=0.28)

    step_state(state, steps=36, directive=directive)

    assert state.lesson_flow.visual_obscurity_risk > 0.5
    assert state.lesson_flow.theory_signal == "supported"
    assert state.lesson_flow.compensation_mode in {"focus-windowed stillness", "anchor recaps", "rhythmic refresh"}
    assert state.lesson_flow.display_clarity < 0.8
    assert state.lesson_flow.final_pace_rate < 0.65