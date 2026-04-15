from __future__ import annotations

import json
from pathlib import Path
import sys
from threading import Thread
from urllib import request


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from cognineuerohub.model import bootstrap_state, step_state
from cognineuerohub.server import CogniNeueroHubHandler, ThreadingHTTPServer


BAVARIA_LESSON = {
    "title": "Medieval Bavaria: duchies, monasteries, and the Wittelsbach rise",
    "subject": "history",
    "region": "Bavaria",
    "era": "900-1300 CE",
    "essential_question": "How did political power, monastic culture, and imperial ties shape medieval Bavaria?",
    "objectives": [
        "Explain how the stem duchy of Bavaria fit into the Holy Roman Empire.",
        "Trace the political significance of the Ottonians, Welfs, and Wittelsbachs.",
        "Connect monastic reform and trade routes to regional power.",
    ],
    "vocabulary": ["duchy", "investiture", "Wittelsbach", "monastery", "Holy Roman Empire"],
}

COURSE_PROFILE = {
    "title": "Bavaria Seminar Spring",
    "educator_name": "Dr. Rowan",
    "god_profile": {
        "conductor_name": "GodAI Seminar Voice",
        "tone": "steady mercy",
        "mercy_bias": 0.82,
        "challenge_bias": 0.61,
        "wonder_bias": 0.85,
    },
    "politeness_protocol": {
        "greeting_template": "Welcome back",
        "affirmation_template": "Thank you for your careful thought",
        "closing_template": "Carry the lesson gently",
        "redirection_template": "Let us return to the core thread",
    },
    "pace_profile": {
        "auto_pace_enabled": True,
        "manual_pace_bias": 0.46,
        "manual_clarity_bias": 0.84,
        "ai_authority": 0.78,
        "target_page_minutes": 5.5,
        "target_puzzle_seconds": 80.0,
        "live_metrics": {
            "page_minutes": 6.8,
            "average_puzzle_seconds": 108.0,
            "last_puzzle_seconds": 124.0,
            "active_activity_seconds": 42.0,
            "solved_activity_count": 2,
        },
    },
    "students": [
        {
            "student_id": "ada-l",
            "display_name": "Ada L.",
            "archetype": "careful synthesizer",
            "strengths": ["pattern recognition"],
            "support_needs": ["spoken recap"],
            "interests": ["maps"],
            "preferred_modalities": ["discussion"],
            "egosphere": {
                "trust": 0.68,
                "fear": 0.3,
                "adaptability": 0.73,
                "reciprocity": 0.59,
                "resonance": 0.81,
                "dominance": 0.22,
            },
            "speech": {"voice_name": "Ada Voice", "voice_hint": "calm", "rate": 0.96, "pitch": 1.02, "volume": 1.0},
        }
    ],
}


def _json_request(url: str, payload: dict | None = None) -> dict:
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    http_request = request.Request(url, data=body, headers=headers, method="POST" if body else "GET")
    with request.urlopen(http_request) as response:
        return json.loads(response.read().decode("utf-8"))


def test_bavaria_lesson_profile_persists_through_simulation_steps():
    state = bootstrap_state(seed=19, agent_count=12, habitat_count=4, lesson=BAVARIA_LESSON, course=COURSE_PROFILE)
    starting_knowledge = state.mean_knowledge

    step_state(state, steps=8)

    assert state.lesson.title == BAVARIA_LESSON["title"]
    assert state.lesson.region == "Bavaria"
    assert state.course.students[0].display_name == "Ada L."
    assert len(state.lesson.objectives) == 3
    assert len(state.lesson_mastery) == 3
    assert state.mastery_overview > 0.0
    assert state.mean_knowledge >= starting_knowledge
    assert 0.0 <= state.hub_consensus <= 1.0


def test_bavaria_lesson_flows_through_http_api():
    server = ThreadingHTTPServer(("127.0.0.1", 0), CogniNeueroHubHandler)
    server.state = bootstrap_state()
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        health = _json_request(f"{base_url}/api/health")
        assert health["ok"] is True

        lessons = _json_request(f"{base_url}/api/lessons")
        assert lessons["lessons"][0]["lesson_id"] == "medieval-bavaria-v1"
        assert "Otto of Freising" in lessons["lessons"][0]["key_figures"]
        assert lessons["lessons"][1]["puzzle"]["type"] == "match_pairs"
        assert lessons["lessons"][0]["activities"][1]["type"] == "multiple_choice"
        assert lessons["lessons"][0]["activities"][2]["type"] == "evidence_select"
        assert lessons["lessons"][0]["activities"][3]["type"] == "custom_game"
        assert lessons["lessons"][0]["activities"][3]["animation_ids"] == ["teddy-bear-scribe", "fawn-route-guide"]
        assert lessons["lessons"][0]["activities"][3]["config"]["correct_order"] == ["monastery", "route", "ducal"]
        assert lessons["lessons"][0]["depth"]["shape"] in {"guided", "seminar-rich"}

        animations = _json_request(f"{base_url}/api/animations")
        assert animations["library_id"] == "lesson-animation-library-v1"
        assert animations["animations"][0]["asset_path"].startswith("/lesson-animations/")
        assert {item["animation_id"] for item in animations["animations"]} >= {"teddy-bear-scribe", "fawn-route-guide"}

        course = _json_request(f"{base_url}/api/course")
        assert course["setup_complete"] is False

        course_setup = _json_request(f"{base_url}/api/course/setup", COURSE_PROFILE)
        assert course_setup["students"][0]["student_id"] == "ada-l"
        assert course_setup["god_profile"]["conductor_name"] == "GodAI Seminar Voice"
        assert course_setup["politeness_protocol"]["greeting_template"] == "Welcome back"

        course_export = _json_request(f"{base_url}/api/course/export")
        assert course_export["course"]["students"][0]["student_id"] == "ada-l"
        assert course_export["version"] == 1

        course_import = _json_request(f"{base_url}/api/course/import", course_export)
        assert course_import["students"][0]["speech"]["voice_name"] == "Ada Voice"

        reset_state = _json_request(
            f"{base_url}/api/reset",
            {
                "seed": 23,
                "agent_count": 10,
                "habitat_count": 3,
                "lesson": BAVARIA_LESSON,
            },
        )
        assert reset_state["lesson"]["title"] == BAVARIA_LESSON["title"]
        assert reset_state["lesson"]["region"] == "Bavaria"
        assert len(reset_state["lesson_mastery"]) == 3

        stepped_state = _json_request(
            f"{base_url}/api/step",
            {
                "steps": 5,
                "lesson": BAVARIA_LESSON,
                "course": COURSE_PROFILE,
                "directive": {
                    "curiosity_bias": 0.84,
                    "equity_bias": 0.77,
                    "challenge_bias": 0.63,
                    "reflection_bias": 0.88,
                },
            },
        )
        assert stepped_state["tick"] == 5
        assert stepped_state["lesson"]["essential_question"] == BAVARIA_LESSON["essential_question"]
        assert stepped_state["lesson"]["vocabulary"][2] == "Wittelsbach"
        assert stepped_state["lesson_mastery"][0]["focus"]
        assert stepped_state["mastery_overview"] > 0.0
        assert 0.0 <= stepped_state["mean_knowledge"] <= 1.0
        assert stepped_state["lesson_flow"]["final_pace_label"] in {"slow and clear", "measured", "brisk"}
        assert stepped_state["lesson_flow"]["auto_run_interval_ms"] > 0

        response_analysis = _json_request(
            f"{base_url}/api/respond",
            {
                "lesson": BAVARIA_LESSON,
                "course": COURSE_PROFILE,
                "student_id": "ada-l",
                "response": "Bavaria was shaped by the Holy Roman Empire, monastery influence, trade, and the Wittelsbach family after investiture conflict.",
            },
        )
        assert response_analysis["analysis"]["keyword_hits"] >= 4
        assert response_analysis["analysis"]["score"] > 0.5
        assert len(response_analysis["analysis"]["dimension_scores"]) >= 3
        assert response_analysis["history"]["lesson_id"]

        student_note = _json_request(
            f"{base_url}/api/student-note",
            {
                "student_id": "ada-l",
                "course": COURSE_PROFILE,
                "lesson": BAVARIA_LESSON,
            },
        )
        assert student_note["student_id"] == "ada-l"
        assert student_note["greeting"].startswith("Welcome back")
        assert student_note["lesson_flow"]["compensation_mode"]
        assert student_note["guidance"]["conductor_name"] == "GodAI Seminar Voice"
        assert student_note["speech"]["voice_hint"] == "calm"

        course_after_note = _json_request(f"{base_url}/api/course")
        assert course_after_note["students"][0]["lesson_history"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)