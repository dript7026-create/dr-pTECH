"""Deterministic ad-planning model for drIpSignalStudio."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import fmean


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass
class BrandProfile:
    brand_name: str = "drIpTECH"
    product_name: str = "Signal Forge"
    audience: str = "builders who need sharper campaign drafts"
    offer: str = "turn complex work into concise visual campaigns"
    tone: str = "incisive, cinematic, optimistic"
    cta: str = "Book a build sprint"
    landing_page: str = "https://example.invalid/driptech"


@dataclass
class SignalSet:
    trend_momentum: float = 0.82
    audience_match: float = 0.77
    proof_strength: float = 0.69
    novelty_gap: float = 0.71
    fatigue_risk: float = 0.28
    conversion_intent: float = 0.74
    retention_pull: float = 0.63


@dataclass(frozen=True)
class SlotSpec:
    key: str
    label: str
    hour: int
    minute: int
    momentum_bias: float
    audience_bias: float
    proof_bias: float
    novelty_bias: float
    conversion_bias: float
    retention_bias: float
    fatigue_penalty: float
    format_bias: str


@dataclass
class SubmissionSlot:
    key: str
    label: str
    clock: str
    score: float
    rationale: str
    format_bias: str


@dataclass
class AdDraft:
    slot_key: str
    slot_label: str
    creative_angle: str
    hook: str
    short_script: list[str]
    long_script: list[str]
    caption: str
    visual_direction: list[str]
    shot_plan: list[str]
    asset_checklist: list[str]
    call_to_action: str
    hashtags: list[str]
    render_assets: dict = field(default_factory=dict)


@dataclass
class CampaignPlan:
    profile: BrandProfile
    signals: SignalSet
    overall_score: float
    market_posture: str
    recommended_windows: list[SubmissionSlot] = field(default_factory=list)
    drafts: list[AdDraft] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


SLOT_SPECS = [
    SlotSpec("ignite", "Ignite Window", 7, 40, 0.92, 0.78, 0.54, 0.86, 0.62, 0.45, 0.16, "velocity cut"),
    SlotSpec("commute", "Commute Window", 9, 5, 0.66, 0.88, 0.58, 0.61, 0.68, 0.44, 0.18, "talking-head snap"),
    SlotSpec("midday", "Midday Window", 11, 55, 0.71, 0.83, 0.72, 0.57, 0.86, 0.49, 0.21, "proof stack"),
    SlotSpec("afternoon", "Afternoon Window", 14, 20, 0.63, 0.69, 0.75, 0.64, 0.79, 0.58, 0.24, "comparison reel"),
    SlotSpec("close", "Close Window", 16, 45, 0.58, 0.76, 0.88, 0.48, 0.91, 0.62, 0.24, "offer close"),
    SlotSpec("prime", "Prime Window", 18, 35, 0.87, 0.84, 0.64, 0.82, 0.77, 0.74, 0.31, "cinematic reveal"),
    SlotSpec("night", "Night Window", 20, 50, 0.69, 0.72, 0.79, 0.73, 0.67, 0.88, 0.27, "story loop"),
    SlotSpec("late", "Late Recall", 22, 10, 0.48, 0.61, 0.71, 0.78, 0.54, 0.92, 0.33, "ambient recap"),
]


def default_payload() -> dict:
    return {
        "profile": asdict(BrandProfile()),
        "signals": asdict(SignalSet()),
    }


def catalog_payload() -> dict:
    return {
        "creative_modes": [
            "velocity cut",
            "proof stack",
            "cinematic reveal",
            "story loop",
            "offer close",
        ],
        "visual_motifs": [
            "text-on-motion punch-ins",
            "macro hands-on process footage",
            "bright product edge-lighting",
            "grid overlays with hard cuts",
            "split-screen before-and-after proof",
        ],
        "signals": [
            "trend_momentum",
            "audience_match",
            "proof_strength",
            "novelty_gap",
            "fatigue_risk",
            "conversion_intent",
            "retention_pull",
        ],
    }


def _slot_score(slot: SlotSpec, signals: SignalSet) -> float:
    score = (
        signals.trend_momentum * slot.momentum_bias
        + signals.audience_match * slot.audience_bias
        + signals.proof_strength * slot.proof_bias
        + signals.novelty_gap * slot.novelty_bias
        + signals.conversion_intent * slot.conversion_bias
        + signals.retention_pull * slot.retention_bias
        - signals.fatigue_risk * slot.fatigue_penalty
    ) / 6.0
    return round(_clamp(score), 3)


def _strongest_signal(signals: SignalSet) -> tuple[str, float]:
    candidates = {
        "trend": signals.trend_momentum,
        "fit": signals.audience_match,
        "proof": signals.proof_strength,
        "novelty": signals.novelty_gap,
        "intent": signals.conversion_intent,
        "retention": signals.retention_pull,
    }
    key = max(candidates, key=candidates.get)
    return key, candidates[key]


def _market_posture(signals: SignalSet) -> str:
    posture_score = fmean(
        [
            signals.trend_momentum,
            signals.audience_match,
            signals.proof_strength,
            signals.novelty_gap,
            signals.conversion_intent,
            signals.retention_pull,
            1.0 - signals.fatigue_risk,
        ]
    )
    if posture_score >= 0.76:
        return "surging"
    if posture_score >= 0.61:
        return "stable-pressure"
    return "rebuild-window"


def _window_rationale(slot: SlotSpec, signals: SignalSet) -> str:
    strongest_signal, strength = _strongest_signal(signals)
    fatigue = 1.0 - signals.fatigue_risk
    return (
        f"{slot.label} favors {slot.format_bias} because {strongest_signal} pressure is "
        f"{strength:.2f} while freshness headroom is {fatigue:.2f}."
    )


def _angle(slot: SubmissionSlot, profile: BrandProfile, signals: SignalSet) -> str:
    strongest_signal, _ = _strongest_signal(signals)
    angle_map = {
        "trend": f"Show how {profile.product_name} rides the current wave without looking derivative.",
        "fit": f"Frame {profile.product_name} as exactly right for {profile.audience}.",
        "proof": f"Lead with visible evidence that {profile.offer} produces cleaner outcomes.",
        "novelty": f"Present a fresh visual ritual that makes {profile.product_name} feel newly urgent.",
        "intent": f"Make the offer frictionless so viewers can move straight toward {profile.cta}.",
        "retention": f"Build a looped narrative that rewards replay and deeper watch time.",
    }
    return angle_map[strongest_signal]


def _hashtags(profile: BrandProfile) -> list[str]:
    brand_tag = "#" + "".join(ch for ch in profile.brand_name.title() if ch.isalnum())
    product_tag = "#" + "".join(ch for ch in profile.product_name.title() if ch.isalnum())
    return [brand_tag, product_tag, "#CreativeOps", "#CampaignDraft", "#BrandSystems"]


def _visual_direction(slot: SubmissionSlot, profile: BrandProfile, signals: SignalSet) -> list[str]:
    motif = [
        "amber edge light over graphite surfaces",
        "fast text cards with two-word punches",
        "clean process footage with visible hand movement",
        "hard-cut overlays showing problem, shift, and payoff",
    ]
    if signals.novelty_gap >= 0.7:
        motif.append("unexpected angle changes every 1.5 seconds")
    if signals.proof_strength >= 0.7:
        motif.append("receipts-on-screen with concise numeric proof")
    if slot.format_bias == "story loop":
        motif.append("ending frame that visually mirrors the opener")
    motif.append(f"title card branded for {profile.brand_name}")
    return motif


def _shot_plan(slot: SubmissionSlot, profile: BrandProfile) -> list[str]:
    return [
        f"Open on the core friction facing {profile.audience}.",
        f"Cut to the working surface where {profile.product_name} changes the pace.",
        "Flash a three-beat proof sequence with numbers or transformed output.",
        f"Close on the offer and direct viewers toward {profile.cta}.",
    ]


def _short_script(slot: SubmissionSlot, profile: BrandProfile) -> list[str]:
    return [
        f"Still doing this the slow way?",
        f"{profile.product_name} turns {profile.offer} into a repeatable move.",
        f"If you're targeting {profile.audience}, this is the faster path.",
        profile.cta,
    ]


def _long_script(slot: SubmissionSlot, profile: BrandProfile) -> list[str]:
    return [
        f"Most teams lose momentum because the message gets muddy before the campaign even starts.",
        f"{profile.product_name} keeps the signal clean: {profile.offer}.",
        f"This {slot.format_bias} piece is timed for {slot.label.lower()} when attention conditions best match manual submission.",
        f"If that matches what {profile.audience} needs, take the next step: {profile.cta}.",
    ]


def _caption(slot: SubmissionSlot, profile: BrandProfile) -> str:
    return (
        f"{slot.label}: a sharper way to present {profile.product_name}. "
        f"Built for {profile.audience}. Offer: {profile.offer}. {profile.cta}."
    )


def _asset_checklist(slot: SubmissionSlot, profile: BrandProfile) -> list[str]:
    return [
        "9:16 master export",
        "1:1 square crop",
        "thumbnail frame with readable four-word hook",
        "caption block and platform description",
        f"landing link for {profile.landing_page}",
    ]


def build_plan(profile: BrandProfile, signals: SignalSet) -> CampaignPlan:
    ranked = sorted(
        [
            SubmissionSlot(
                key=slot.key,
                label=slot.label,
                clock=f"{slot.hour:02d}:{slot.minute:02d}",
                score=_slot_score(slot, signals),
                rationale=_window_rationale(slot, signals),
                format_bias=slot.format_bias,
            )
            for slot in SLOT_SPECS
        ],
        key=lambda item: item.score,
        reverse=True,
    )[:5]

    drafts = []
    for slot in ranked:
        drafts.append(
            AdDraft(
                slot_key=slot.key,
                slot_label=slot.label,
                creative_angle=_angle(slot, profile, signals),
                hook=f"{profile.product_name}: move faster without flattening the message.",
                short_script=_short_script(slot, profile),
                long_script=_long_script(slot, profile),
                caption=_caption(slot, profile),
                visual_direction=_visual_direction(slot, profile, signals),
                shot_plan=_shot_plan(slot, profile),
                asset_checklist=_asset_checklist(slot, profile),
                call_to_action=profile.cta,
                hashtags=_hashtags(profile),
            )
        )

    overall_score = round(
        fmean(
            [
                signals.trend_momentum,
                signals.audience_match,
                signals.proof_strength,
                signals.novelty_gap,
                signals.conversion_intent,
                signals.retention_pull,
                1.0 - signals.fatigue_risk,
            ]
        ),
        3,
    )

    return CampaignPlan(
        profile=profile,
        signals=signals,
        overall_score=overall_score,
        market_posture=_market_posture(signals),
        recommended_windows=ranked,
        drafts=drafts,
    )


def coerce_profile(payload: dict | None) -> BrandProfile:
    payload = payload or {}
    return BrandProfile(
        brand_name=str(payload.get("brand_name", BrandProfile.brand_name)),
        product_name=str(payload.get("product_name", BrandProfile.product_name)),
        audience=str(payload.get("audience", BrandProfile.audience)),
        offer=str(payload.get("offer", BrandProfile.offer)),
        tone=str(payload.get("tone", BrandProfile.tone)),
        cta=str(payload.get("cta", BrandProfile.cta)),
        landing_page=str(payload.get("landing_page", BrandProfile.landing_page)),
    )


def coerce_signals(payload: dict | None) -> SignalSet:
    payload = payload or {}
    return SignalSet(
        trend_momentum=_clamp(payload.get("trend_momentum", SignalSet.trend_momentum)),
        audience_match=_clamp(payload.get("audience_match", SignalSet.audience_match)),
        proof_strength=_clamp(payload.get("proof_strength", SignalSet.proof_strength)),
        novelty_gap=_clamp(payload.get("novelty_gap", SignalSet.novelty_gap)),
        fatigue_risk=_clamp(payload.get("fatigue_risk", SignalSet.fatigue_risk)),
        conversion_intent=_clamp(payload.get("conversion_intent", SignalSet.conversion_intent)),
        retention_pull=_clamp(payload.get("retention_pull", SignalSet.retention_pull)),
    )