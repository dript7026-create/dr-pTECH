from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .adapters import AdapterSnapshot, BaseAdapter, Mutation
from .authorization import AuthorizationScope, MutationDomain, safe_profile
from .coherency import CoherencyField, CoherencySignal


def clamp_unit(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


@dataclass
class KaijuGaidenRuntimeAdapter(BaseAdapter):
    target_name: str = "host"
    scene_id: str = "harbor_boss_duel"
    scene_type: str = "boss-rush"
    encounter_pressure: float = 0.63
    silhouette_density: float = 0.72
    moisture_retention: float = 0.58
    air_reactivity: float = 0.44
    particle_shed: float = 0.61
    toxicants: float = 0.33
    insolvent_impurities: float = 0.29
    atmospheric_corrosives: float = 0.31
    atmospheric_irritants: float = 0.36
    respiratory_burden: float = 0.34
    hemoneural_stress: float = 0.27
    plasmic_instability: float = 0.24
    matter_tension_stasis: float = 0.21
    hit_precision: float = 0.68
    predictive_share: float = 0.46
    adaptive_share: float = 0.64
    field_stability: float = 0.0
    field_tension: float = 0.0
    field_resonance: float = 0.0
    field_coherence: float = 0.0

    def snapshot(self) -> AdapterSnapshot:
        return AdapterSnapshot(
            name=self.name,
            summary="KaijuGaiden boss-runtime bridge",
            signals=[
                CoherencySignal("encounter_pressure", 9.2, self.encounter_pressure, 0.61, 0.91),
                CoherencySignal("silhouette_density", 7.4, self.silhouette_density, 0.52, 0.94),
                CoherencySignal("moisture_retention", 5.8, self.moisture_retention, 0.47, 0.88),
                CoherencySignal("air_reactivity", 6.6, self.air_reactivity, 0.58, 0.84),
                CoherencySignal("toxicants", 7.1, self.toxicants, 0.42, 0.89),
                CoherencySignal("insolvent_impurities", 6.9, self.insolvent_impurities, 0.38, 0.81),
                CoherencySignal("atmospheric_corrosives", 7.5, self.atmospheric_corrosives, 0.41, 0.85),
                CoherencySignal("atmospheric_irritants", 7.8, self.atmospheric_irritants, 0.46, 0.88),
                CoherencySignal("respiratory_burden", 8.0, self.respiratory_burden, 0.44, 0.86),
                CoherencySignal("hit_precision", 10.1, self.hit_precision, 0.49, 0.92),
            ],
            metrics={
                "encounter_pressure": self.encounter_pressure,
                "silhouette_density": self.silhouette_density,
                "moisture_retention": self.moisture_retention,
                "air_reactivity": self.air_reactivity,
                "particle_shed": self.particle_shed,
                "toxicants": self.toxicants,
                "insolvent_impurities": self.insolvent_impurities,
                "atmospheric_corrosives": self.atmospheric_corrosives,
                "atmospheric_irritants": self.atmospheric_irritants,
                "respiratory_burden": self.respiratory_burden,
                "hemoneural_stress": self.hemoneural_stress,
                "plasmic_instability": self.plasmic_instability,
                "matter_tension_stasis": self.matter_tension_stasis,
                "hit_precision": self.hit_precision,
                "predictive_share": self.predictive_share,
                "adaptive_share": self.adaptive_share,
                "field_stability": self.field_stability,
                "field_tension": self.field_tension,
                "field_resonance": self.field_resonance,
                "field_coherence": self.field_coherence,
            },
        )

    def propose_mutations(self, field: CoherencyField):
        self.field_stability = field.stability
        self.field_tension = field.tension
        self.field_resonance = field.resonance
        self.field_coherence = field.coherence_index
        yield Mutation(MutationDomain.PARAMETERS, "encounter_pressure", clamp_unit(field.tension + 0.24, 0.25, 0.96))
        yield Mutation(MutationDomain.PARAMETERS, "silhouette_density", clamp_unit(field.coherence_index * 0.55 + field.stability * 0.45, 0.35, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "moisture_retention", clamp_unit(field.resonance * 0.7 + field.stability * 0.3, 0.15, 0.95))
        yield Mutation(MutationDomain.PARAMETERS, "air_reactivity", clamp_unit(field.tension * 0.6 + (1.0 - field.stability) * 0.4, 0.1, 0.95))
        yield Mutation(MutationDomain.PARAMETERS, "particle_shed", clamp_unit(field.tension * 0.55 + field.resonance * 0.45, 0.1, 1.0))
        yield Mutation(MutationDomain.PARAMETERS, "toxicants", clamp_unit(field.tension * 0.5 + (1.0 - field.stability) * 0.3 + field.resonance * 0.2, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "insolvent_impurities", clamp_unit(field.tension * 0.35 + (1.0 - field.coherence_index) * 0.4 + field.resonance * 0.25, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "atmospheric_corrosives", clamp_unit(field.tension * 0.45 + field.resonance * 0.25 + (1.0 - field.stability) * 0.3, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "atmospheric_irritants", clamp_unit(field.tension * 0.4 + (1.0 - field.stability) * 0.25 + (1.0 - field.coherence_index) * 0.35, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "respiratory_burden", clamp_unit(field.tension * 0.3 + (1.0 - field.stability) * 0.3 + field.resonance * 0.15 + (1.0 - field.coherence_index) * 0.25, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "hemoneural_stress", clamp_unit(field.tension * 0.35 + (1.0 - field.coherence_index) * 0.4 + (1.0 - field.stability) * 0.25, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "plasmic_instability", clamp_unit(field.resonance * 0.45 + field.tension * 0.25 + (1.0 - field.stability) * 0.3, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "matter_tension_stasis", clamp_unit(field.stability * 0.25 + field.tension * 0.4 + (1.0 - field.coherence_index) * 0.35, 0.05, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "hit_precision", clamp_unit(field.coherence_index * 0.6 + field.stability * 0.4, 0.2, 0.98))
        yield Mutation(MutationDomain.PARAMETERS, "predictive_share", clamp_unit(field.coherence_index * 0.45 + field.stability * 0.35 + (1.0 - field.tension) * 0.2, 0.05, 0.95))
        yield Mutation(MutationDomain.PARAMETERS, "adaptive_share", clamp_unit(field.resonance * 0.45 + field.tension * 0.3 + field.coherence_index * 0.25, 0.05, 0.98))

    def _apply_mutation(self, mutation: Mutation) -> None:
        if mutation.key == "encounter_pressure":
            self.encounter_pressure = mutation.value
        elif mutation.key == "silhouette_density":
            self.silhouette_density = mutation.value
        elif mutation.key == "moisture_retention":
            self.moisture_retention = mutation.value
        elif mutation.key == "air_reactivity":
            self.air_reactivity = mutation.value
        elif mutation.key == "particle_shed":
            self.particle_shed = mutation.value
        elif mutation.key == "toxicants":
            self.toxicants = mutation.value
        elif mutation.key == "insolvent_impurities":
            self.insolvent_impurities = mutation.value
        elif mutation.key == "atmospheric_corrosives":
            self.atmospheric_corrosives = mutation.value
        elif mutation.key == "atmospheric_irritants":
            self.atmospheric_irritants = mutation.value
        elif mutation.key == "respiratory_burden":
            self.respiratory_burden = mutation.value
        elif mutation.key == "hemoneural_stress":
            self.hemoneural_stress = mutation.value
        elif mutation.key == "plasmic_instability":
            self.plasmic_instability = mutation.value
        elif mutation.key == "matter_tension_stasis":
            self.matter_tension_stasis = mutation.value
        elif mutation.key == "hit_precision":
            self.hit_precision = mutation.value
        elif mutation.key == "predictive_share":
            self.predictive_share = mutation.value
        elif mutation.key == "adaptive_share":
            self.adaptive_share = mutation.value


def build_kaijugaiden_adapter(
    preset: str = "default",
    scene_id: str = "harbor_boss_duel",
    scene_type: str = "boss-rush",
) -> KaijuGaidenRuntimeAdapter:
    adapter = KaijuGaidenRuntimeAdapter(
        name="kaijugaiden",
        authorization=safe_profile(AuthorizationScope.ENGINE),
        scene_id=scene_id,
        scene_type=scene_type,
    )
    if preset == "storm":
        adapter.encounter_pressure = 0.82
        adapter.silhouette_density = 0.78
        adapter.moisture_retention = 0.69
        adapter.air_reactivity = 0.63
        adapter.particle_shed = 0.80
        adapter.toxicants = 0.58
        adapter.insolvent_impurities = 0.46
        adapter.atmospheric_corrosives = 0.52
        adapter.atmospheric_irritants = 0.57
        adapter.respiratory_burden = 0.49
        adapter.hemoneural_stress = 0.43
        adapter.plasmic_instability = 0.41
        adapter.matter_tension_stasis = 0.46
        adapter.hit_precision = 0.74
        adapter.predictive_share = 0.42
        adapter.adaptive_share = 0.78
    elif preset == "calm":
        adapter.encounter_pressure = 0.34
        adapter.silhouette_density = 0.60
        adapter.moisture_retention = 0.46
        adapter.air_reactivity = 0.24
        adapter.particle_shed = 0.29
        adapter.toxicants = 0.14
        adapter.insolvent_impurities = 0.12
        adapter.atmospheric_corrosives = 0.13
        adapter.atmospheric_irritants = 0.16
        adapter.respiratory_burden = 0.14
        adapter.hemoneural_stress = 0.12
        adapter.plasmic_instability = 0.11
        adapter.matter_tension_stasis = 0.10
        adapter.hit_precision = 0.64
        adapter.predictive_share = 0.62
        adapter.adaptive_share = 0.41
    return adapter


def build_kaijugaiden_runtime_contract(adapter: KaijuGaidenRuntimeAdapter) -> dict[str, object]:
    volumetric_support = clamp_unit((adapter.particle_shed + adapter.moisture_retention) / 2.0, 0.1, 1.0)
    hope_clog_risk = clamp_unit(adapter.air_reactivity * (1.0 - adapter.moisture_retention) + adapter.particle_shed * 0.35 + adapter.insolvent_impurities * 0.25 + adapter.atmospheric_irritants * 0.15 - adapter.adaptive_share * 0.15, 0.0, 1.0)
    render_reactivity = clamp_unit(adapter.particle_shed * 0.65 + adapter.encounter_pressure * 0.35, 0.05, 1.0)
    volumetric_bias = clamp_unit(adapter.moisture_retention * 0.55 + adapter.particle_shed * 0.45, 0.05, 1.0)
    matter_reactive_volume = round(32.0 + adapter.moisture_retention * 20.0 + adapter.adaptive_share * 24.0 + adapter.toxicants * 8.0, 2)
    anim_blend_ms_base = round(96.0 - adapter.hit_precision * 34.0 - adapter.adaptive_share * 18.0 + adapter.particle_shed * 10.0, 2)
    timeline_project_progress = clamp_unit(adapter.predictive_share * 0.22 + adapter.adaptive_share * 0.24 + adapter.field_coherence * 0.16 + adapter.field_stability * 0.10 + adapter.encounter_pressure * 0.14 + adapter.hit_precision * 0.14, 0.05, 1.0)
    timeline_predictive_vision = clamp_unit(adapter.predictive_share * 0.48 + adapter.field_coherence * 0.20 + adapter.hit_precision * 0.18 + adapter.encounter_pressure * 0.08 + adapter.particle_shed * 0.06, 0.05, 1.0)
    timeline_refinement_depth = clamp_unit(adapter.adaptive_share * 0.34 + adapter.field_resonance * 0.18 + adapter.silhouette_density * 0.16 + adapter.hit_precision * 0.16 + adapter.moisture_retention * 0.08 + adapter.particle_shed * 0.08, 0.05, 1.0)
    timeline_derivative_final_state = clamp_unit(timeline_project_progress * 0.26 + timeline_predictive_vision * 0.28 + timeline_refinement_depth * 0.22 + adapter.field_tension * 0.12 + adapter.plasmic_instability * 0.12, 0.05, 1.0)
    return {
        "project_name": "Kaiju Gaiden",
        "primary_target": adapter.target_name,
        "runtime": {
            "entry_scene": adapter.scene_id,
            "system_graph": [
                "combat",
                "boss_motion",
                "timeline_projection_layer",
                "silhouette_hit_detection",
                "environmental_regen",
                "fx_audio_bridge",
            ],
            "timeline": {
                "project_progress": round(timeline_project_progress, 4),
                "predictive_vision": round(timeline_predictive_vision, 4),
                "derivative_final_state": round(timeline_derivative_final_state, 4),
                "refinement_depth": round(timeline_refinement_depth, 4),
            },
        },
        "targets": [
            {
                "name": adapter.target_name,
                "input_latency_ms": round(8.0 + (1.0 - adapter.hit_precision) * 6.0, 2),
                "present_budget_ms": 16.67,
                "render_scale": 1.0,
                "handheld_bias": 0.25,
                "sensor_channels": 1,
                "volumetric_support": round(volumetric_support, 4),
                "causality_feedback": round(clamp_unit(adapter.encounter_pressure * 0.5 + adapter.adaptive_share * 0.5, 0.05, 1.0), 4),
            }
        ],
        "bridgeTargetName": adapter.target_name,
        "bridgeInputLatencyMs": round(8.0 + (1.0 - adapter.hit_precision) * 6.0, 2),
        "bridgePresentBudgetMs": 16.67,
        "bridgeRenderScale": 1.0,
        "bridgeHandheldBias": 0.25,
        "bridgeSensorChannels": 1,
        "bridgeVolumetricSupport": round(volumetric_support, 4),
        "bridgeCausalityFeedback": round(clamp_unit(adapter.encounter_pressure * 0.5 + adapter.adaptive_share * 0.5, 0.05, 1.0), 4),
        "bridgeSceneId": adapter.scene_id,
        "bridgeSceneType": adapter.scene_type,
        "bridgeMatterSolidDensity": round(clamp_unit(adapter.silhouette_density * 0.65 + adapter.hit_precision * 0.35, 0.1, 1.0), 4),
        "bridgeMatterLiquidFlow": round(clamp_unit(adapter.moisture_retention, 0.05, 1.0), 4),
        "bridgeMatterGasDiffusion": round(clamp_unit(adapter.air_reactivity, 0.05, 1.0), 4),
        "bridgeMatterFluidTurbulence": round(clamp_unit(adapter.particle_shed * 0.7 + adapter.encounter_pressure * 0.3, 0.05, 1.0), 4),
        "bridgeMatterReactiveVolume": matter_reactive_volume,
        "bridgeMatterToxicants": round(clamp_unit(adapter.toxicants, 0.0, 1.0), 4),
        "bridgeMatterInsolventImpurities": round(clamp_unit(adapter.insolvent_impurities, 0.0, 1.0), 4),
        "bridgeAtmosphericCorrosives": round(clamp_unit(adapter.atmospheric_corrosives, 0.0, 1.0), 4),
        "bridgeAtmosphericIrritants": round(clamp_unit(adapter.atmospheric_irritants, 0.0, 1.0), 4),
        "bridgeRespiratoryBurden": round(clamp_unit(adapter.respiratory_burden, 0.0, 1.0), 4),
        "bridgeHemoneuralStress": round(clamp_unit(adapter.hemoneural_stress, 0.0, 1.0), 4),
        "bridgePlasmicInstability": round(clamp_unit(adapter.plasmic_instability, 0.0, 1.0), 4),
        "bridgeMatterTensionStasis": round(clamp_unit(adapter.matter_tension_stasis, 0.0, 1.0), 4),
        "bridgeInputPressure": round(clamp_unit(adapter.encounter_pressure, 0.05, 1.0), 4),
        "bridgeEntityFeedback": round(clamp_unit(adapter.adaptive_share * 0.55 + adapter.hit_precision * 0.45, 0.05, 1.0), 4),
        "bridgeRenderReactivity": round(render_reactivity, 4),
        "bridgeVolumetricBias": round(volumetric_bias, 4),
        "bridgeAffordanceSpan": round(clamp_unit(adapter.hit_precision * 0.5 + adapter.predictive_share * 0.5, 0.05, 1.0), 4),
        "bridgeHopeTheta": round(clamp_unit(adapter.field_resonance * 0.5 + adapter.field_coherence * 0.5, 0.0, 1.0), 4),
        "bridgeHopeClogRisk": round(hope_clog_risk, 4),
        "bridgeHopePredictiveShare": round(clamp_unit(adapter.predictive_share, 0.0, 1.0), 4),
        "bridgeHopeAdaptiveShare": round(clamp_unit(adapter.adaptive_share, 0.0, 1.0), 4),
        "bridgeInteractionDensityHint": round(clamp_unit(adapter.encounter_pressure * 0.6 + adapter.particle_shed * 0.4, 0.05, 1.0), 4),
        "bridgeHitboxActiveRatioHint": round(clamp_unit(adapter.silhouette_density, 0.05, 1.0), 4),
        "bridgeContactAccuracyHint": round(clamp_unit(adapter.hit_precision, 0.05, 1.0), 4),
        "bridgeVfxLoadHint": round(clamp_unit(adapter.particle_shed, 0.05, 1.0), 4),
        "bridgeAnimBlendMsBase": anim_blend_ms_base,
        "bridgeTimelineProjectProgress": round(timeline_project_progress, 4),
        "bridgeTimelinePredictiveVision": round(timeline_predictive_vision, 4),
        "bridgeTimelineDerivativeFinalState": round(timeline_derivative_final_state, 4),
        "bridgeTimelineRefinementDepth": round(timeline_refinement_depth, 4),
    }


def export_kaijugaiden_runtime_contract(adapter: KaijuGaidenRuntimeAdapter, out_path: str | Path) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_kaijugaiden_runtime_contract(adapter)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path