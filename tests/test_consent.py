import pandas as pd

from football_predictor.consent import build_fixture_consent_frame, load_player_consent_manifest


def test_build_fixture_consent_frame_aggregates_team_ratios_and_registry():
    fixtures = pd.DataFrame(
        [
            {
                "home_team": "TeamA",
                "away_team": "TeamB",
                "date": "2026-03-20",
            }
        ]
    )
    consent = pd.DataFrame(
        [
            {"fixture_key": "teama::teamb::2026-03-20", "team": "TeamA", "entity_id": f"teama_{index:02d}", "approved": index <= 11}
            for index in range(1, 12)
        ]
        + [
            {"fixture_key": "teama::teamb::2026-03-20", "team": "TeamB", "entity_id": f"teamb_{index:02d}", "approved": index <= 6}
            for index in range(1, 12)
        ]
    )
    frame = build_fixture_consent_frame(fixtures, consent)
    assert round(float(frame.iloc[0]["home_lineup_approval_ratio"]), 4) == 1.0
    assert round(float(frame.iloc[0]["away_lineup_approval_ratio"]), 4) == round(6 / 11, 4)
    assert float(frame.iloc[0]["lineup_approval_ratio"]) == float(frame.iloc[0]["away_lineup_approval_ratio"])
    assert "teama_01" in frame.iloc[0]["home_consent_registry_json"]


def test_load_player_consent_manifest_keeps_audit_and_expiry_fields(tmp_path):
        path = tmp_path / "consent_manifest.json"
        path.write_text(
                """
{
    "consents": [
        {
            "team": "TeamA",
            "approved": true,
            "home_team": "TeamA",
            "away_team": "TeamB",
            "date": "2026-03-20",
            "entity_id": "teama_01",
            "approval_scope": "play",
            "approval_source": "manifest",
            "approval_granted_at": "2026-03-15T08:30:00Z",
            "approval_expires_at": "2026-03-20T23:59:59Z",
            "audit_ref": "audit-123",
            "play_scope": "minute_1_15",
            "consent_version": "v2"
        }
    ]
}
                """.strip(),
                encoding="utf-8",
        )
        frame = load_player_consent_manifest(str(path))
        assert frame.iloc[0]["approval_scope"] == "play"
        assert frame.iloc[0]["audit_ref"] == "audit-123"
        assert frame.iloc[0]["approval_expires_at"] == "2026-03-20T23:59:59Z"
