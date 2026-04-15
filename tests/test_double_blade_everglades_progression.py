import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_source() -> dict:
    path = ROOT / "DoubleBladeEverGlades" / "double_blade_everglades_project.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_builder_module():
    import importlib.util

    module_path = ROOT / "DoubleBladeEverGlades" / "tools" / "build_progression_manifest.py"
    spec = importlib.util.spec_from_file_location("double_blade_builder", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_progression_manifest_counts_match_design_contract():
    source = load_source()
    builder = load_builder_module()
    manifest = builder.build_progression(source)

    assert manifest["catalog_summary"]["blade_variants"] == 1064
    assert manifest["catalog_summary"]["items"] == 32
    assert manifest["catalog_summary"]["skills"] == 13
    assert manifest["catalog_summary"]["enemy_varieties"] == 230
    assert manifest["catalog_summary"]["rootknots"] == 11


def test_progression_pressure_and_precision_rise_monotonically():
    source = load_source()
    builder = load_builder_module()
    manifest = builder.build_progression(source)
    acts = manifest["progression"]["acts"]

    pressures = [act["pressure"] for act in acts]
    precisions = [act["precision_demand"] for act in acts]
    mutations = [act["mutation_complexity"] for act in acts]

    assert pressures == sorted(pressures)
    assert precisions == sorted(precisions)
    assert mutations == sorted(mutations)


def test_rootknots_cover_route_from_start_to_mother_verge():
    source = load_source()
    builder = load_builder_module()
    manifest = builder.build_progression(source)
    rootknots = manifest["progression"]["rootknots"]

    assert rootknots[0]["progress"] == 0.0
    assert rootknots[-1]["progress"] == 1.0
    assert manifest["progression"]["final_destination"]["furthest_rootknot"] == rootknots[-1]["id"]
    assert all(item["functions"] == ["rest", "fast_travel", "growth_hub"] for item in rootknots)


def test_skill_unlocks_are_assigned_once_across_rootknots():
    source = load_source()
    builder = load_builder_module()
    manifest = builder.build_progression(source)
    rootknots = manifest["progression"]["rootknots"]
    skill_ids = {skill["id"] for skill in manifest["skills"]}
    assigned = []
    for rootknot in rootknots:
        assigned.extend(rootknot.get("unlocks", []))

    assert set(assigned) == skill_ids
    assert len(assigned) == len(skill_ids)


def test_acts_cover_route_without_gaps_and_growth_rating_rises():
    source = load_source()
    builder = load_builder_module()
    manifest = builder.build_progression(source)
    acts = manifest["progression"]["acts"]
    rootknots = manifest["progression"]["rootknots"]

    assert acts[0]["distance_band"][0] == 0.0
    assert acts[-1]["distance_band"][1] == 1.0
    for current, nxt in zip(acts, acts[1:]):
        assert current["distance_band"][1] == nxt["distance_band"][0]

    growth_ratings = [rootknot["growth_rating"] for rootknot in rootknots]
    cumulative_unlocks = [rootknot["cumulative_skill_unlocks"] for rootknot in rootknots]
    assert growth_ratings == sorted(growth_ratings)
    assert cumulative_unlocks == sorted(cumulative_unlocks)