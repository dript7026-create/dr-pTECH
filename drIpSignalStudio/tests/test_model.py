from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dripsignalstudio.model import BrandProfile, SignalSet, build_plan, catalog_payload, default_payload
from dripsignalstudio.render import ensure_render_assets


def test_build_plan_returns_five_ranked_windows_and_matching_drafts():
    plan = build_plan(BrandProfile(), SignalSet())

    assert len(plan.recommended_windows) == 5
    assert len(plan.drafts) == 5
    assert plan.recommended_windows[0].score >= plan.recommended_windows[-1].score
    assert {draft.slot_key for draft in plan.drafts} == {slot.key for slot in plan.recommended_windows}


def test_high_fatigue_penalizes_overall_score():
    low_fatigue = build_plan(BrandProfile(), SignalSet(fatigue_risk=0.1))
    high_fatigue = build_plan(BrandProfile(), SignalSet(fatigue_risk=0.9))

    assert low_fatigue.overall_score > high_fatigue.overall_score


def test_default_and_catalog_payloads_expose_expected_keys():
    defaults = default_payload()
    catalog = catalog_payload()

    assert "profile" in defaults
    assert "signals" in defaults
    assert "creative_modes" in catalog
    assert "signals" in catalog


def test_render_assets_generate_poster_and_optional_video():
    plan = build_plan(BrandProfile(), SignalSet())
    assets = ensure_render_assets(plan, plan.drafts[0])

    assert assets["poster_path"].startswith("/generated/previews/")
    poster_disk_path = Path(__file__).resolve().parents[1] / assets["poster_path"].lstrip("/")
    assert poster_disk_path.exists()
    assert assets["mode"] in {"poster-only", "mp4-preview"}

    if assets["video_path"] is not None:
        video_disk_path = Path(__file__).resolve().parents[1] / assets["video_path"].lstrip("/")
        assert video_disk_path.exists()