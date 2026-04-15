"""Deterministic education-oriented cognition simulation for CogniNeueroHub."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from random import Random
from statistics import fmean


DATA_ROOT = Path(__file__).resolve().parent / "data"
DEFAULT_DATASET_FILE = DATA_ROOT / "artisapiens_seed_v1.json"
DEFAULT_LESSON_LIBRARY_FILE = DATA_ROOT / "lesson_library_v1.json"
DEFAULT_ANIMATION_LIBRARY_FILE = DATA_ROOT / "animation_library_v1.json"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class EquationSpec:
    key: str
    expression: str
    description: str


EQUATION_SPECS = {
    "environment_affordance": EquationSpec(
        key="environment_affordance",
        expression="E = clamp(0.45*stability + 0.35*nutrient + 0.20*complexity)",
        description="Habitat support for safe and interesting learning.",
    ),
    "learning_gain": EquationSpec(
        key="learning_gain",
        expression="L = clamp(0.30*curiosity + 0.25*challenge + 0.25*affordance + 0.20*(1-stress))",
        description="Knowledge gain produced by curiosity, challenge, and environmental support.",
    ),
    "reflective_balance": EquationSpec(
        key="reflective_balance",
        expression="R = clamp(0.35*awareness + 0.30*empathy + 0.20*reflection + 0.15*(1-stress))",
        description="Metacognitive stability that resists panic and impulsive drift.",
    ),
    "social_coherence": EquationSpec(
        key="social_coherence",
        expression="S = clamp(0.40*belonging + 0.35*trust + 0.25*equity)",
        description="Group cohesion under educational equity pressure.",
    ),
    "hub_consensus": EquationSpec(
        key="hub_consensus",
        expression="H = clamp(0.35*mean(knowledge) + 0.25*mean(reflection) + 0.25*mean(coherence) + 0.15*(1*friction))",
        description="Whole-hub consensus signal used by the live dashboard.",
    ),
    "lesson_mastery": EquationSpec(
        key="lesson_mastery",
        expression="M = clamp(wk*knowledge + wr*reflection + wc*coherence + ws*(1-friction) + wi*inquiry)",
        description="Objective-level lesson readiness blended from knowledge, reflection, coherence, calm, and inquiry signals.",
    ),
}


@dataclass
class Directive:
    curiosity_bias: float = 0.72
    equity_bias: float = 0.78
    challenge_bias: float = 0.66
    reflection_bias: float = 0.81


@dataclass
class LessonPhase:
    title: str = ""
    purpose: str = ""
    facilitator_move: str = ""
    learner_signal: str = ""


@dataclass
class ConceptThread:
    label: str = ""
    question: str = ""
    significance: str = ""


@dataclass
class LessonActivity:
    activity_id: str = ""
    type: str = ""
    title: str = ""
    prompt: str = ""
    description: str = ""
    success_message: str = ""
    items: list[dict[str, str]] = field(default_factory=list)
    pairs: list[dict[str, str]] = field(default_factory=list)
    choices: list[str] = field(default_factory=list)
    answer_index: int = 0
    explanation: str = ""
    difficulty: str = "steady"
    animation_ids: list[str] = field(default_factory=list)
    config: dict[str, object] = field(default_factory=dict)


@dataclass
class LessonRubricDimension:
    key: str = ""
    label: str = ""
    weight: float = 0.0
    guidance: str = ""


@dataclass
class LessonDepthProfile:
    phase_count: int = 0
    thread_count: int = 0
    activity_count: int = 0
    rubric_count: int = 0
    depth_score: float = 0.0
    shape: str = "minimal"


@dataclass
class LessonFlowProfile:
    pace_pressure: float = 0.0
    erraticism: float = 0.0
    long_term_drag: float = 0.0
    page_duration_drag: float = 0.0
    solve_speed_drag: float = 0.0
    visual_obscurity_risk: float = 0.0
    display_clarity: float = 1.0
    compensation_strength: float = 0.0
    compensation_mode: str = "steady seminar"
    theory_signal: str = "not-tested"
    final_pace_rate: float = 0.5
    final_pace_label: str = "measured"
    recommended_step_count: int = 6
    auto_run_interval_ms: int = 1200
    educator_prompt: str = "Keep a steady seminar pace."
    learner_prompt: str = "Stay with one anchor at a time."
    feed_opacity: float = 1.0
    animation_scale: float = 1.0


@dataclass
class LivePaceMetrics:
    page_minutes: float = 0.0
    average_puzzle_seconds: float = 0.0
    last_puzzle_seconds: float = 0.0
    active_activity_seconds: float = 0.0
    solved_activity_count: int = 0


@dataclass
class CoursePaceProfile:
    reveal_controls: bool = False
    auto_pace_enabled: bool = True
    manual_pace_bias: float = 0.5
    manual_clarity_bias: float = 0.72
    ai_authority: float = 0.62
    target_page_minutes: float = 6.0
    target_puzzle_seconds: float = 90.0
    live_metrics: LivePaceMetrics = field(default_factory=LivePaceMetrics)


@dataclass
class StudentEgosphere:
    trust: float = 0.5
    fear: float = 0.25
    adaptability: float = 0.5
    reciprocity: float = 0.5
    resonance: float = 0.5
    dominance: float = 0.0


@dataclass
class StudentSpeechProfile:
    voice_hint: str = ""
    voice_name: str = ""
    rate: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0


@dataclass
class StudentLessonHistory:
    lesson_id: str = ""
    lesson_title: str = ""
    visits: int = 0
    last_tick: int = 0
    mastery_overview: float = 0.0
    response_score: float = 0.0
    focus_objective: str = ""
    visual_obscurity_risk: float = 0.0
    compensation_mode: str = "steady seminar"
    greeting: str = ""


@dataclass
class StudentProfile:
    student_id: str = ""
    display_name: str = ""
    archetype: str = "steady learner"
    strengths: list[str] = field(default_factory=list)
    support_needs: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    preferred_modalities: list[str] = field(default_factory=list)
    notes: str = ""
    spiritual_frame: str = "reflective"
    egosphere: StudentEgosphere = field(default_factory=StudentEgosphere)
    speech: StudentSpeechProfile = field(default_factory=StudentSpeechProfile)
    lesson_history: list[StudentLessonHistory] = field(default_factory=list)


@dataclass
class CoursePolitenessProtocol:
    greeting_template: str = "Good to see you"
    affirmation_template: str = "Thank you for your thoughtful work"
    closing_template: str = "Take your time and proceed with care"
    redirection_template: str = "Let us return to one anchor at a time"


@dataclass
class CourseGodProfile:
    conductor_name: str = "GodAI Seminar Voice"
    tone: str = "steady mercy"
    mercy_bias: float = 0.78
    challenge_bias: float = 0.62
    wonder_bias: float = 0.81


@dataclass
class CourseProfile:
    course_id: str = "course-in-formation"
    title: str = "Untitled Course"
    educator_name: str = ""
    course_notes: str = ""
    active_student_id: str = ""
    setup_complete: bool = False
    god_profile: CourseGodProfile = field(default_factory=CourseGodProfile)
    politeness_protocol: CoursePolitenessProtocol = field(default_factory=CoursePolitenessProtocol)
    pace_profile: CoursePaceProfile = field(default_factory=CoursePaceProfile)
    students: list[StudentProfile] = field(default_factory=list)


@dataclass
class LessonProfile:
    lesson_id: str = ""
    title: str = ""
    subject: str = ""
    region: str = ""
    era: str = ""
    essential_question: str = ""
    objectives: list[str] = field(default_factory=list)
    vocabulary: list[str] = field(default_factory=list)
    key_figures: list[str] = field(default_factory=list)
    eras: list[str] = field(default_factory=list)
    source_excerpt: str = ""
    source_attribution: str = ""
    teaching_notes: list[str] = field(default_factory=list)
    discussion_prompts: list[str] = field(default_factory=list)
    phases: list[LessonPhase] = field(default_factory=list)
    concept_threads: list[ConceptThread] = field(default_factory=list)
    response_prompt: str = ""
    response_keywords: list[str] = field(default_factory=list)
    animation_ids: list[str] = field(default_factory=list)
    activities: list[LessonActivity] = field(default_factory=list)
    puzzle: dict[str, object] = field(default_factory=dict)
    response_rubric: list[LessonRubricDimension] = field(default_factory=list)
    objective_weights: list[dict[str, float]] = field(default_factory=list)
    recommended_directive: dict[str, float] = field(default_factory=dict)


@dataclass
class LessonObjectiveMastery:
    objective: str
    score: float
    focus: str


@dataclass
class LessonResponseScore:
    score: float
    keyword_hits: int
    keyword_total: int
    coverage: float
    calm_alignment: float
    inquiry_alignment: float
    feedback: str
    dimension_scores: list[dict[str, object]] = field(default_factory=list)


@dataclass
class StudentLessonNote:
    student_id: str
    student_name: str
    lesson_id: str
    specialized_note: str
    educator_note: str
    speech_text: str
    greeting: str
    closing: str
    history_digest: str
    focus_objective: str
    guidance: dict[str, object]
    lesson_flow: dict[str, object]
    politeness_protocol: dict[str, str]
    egosphere: dict[str, float]
    speech: dict[str, object]


def _default_response_rubric() -> list[LessonRubricDimension]:
    return [
        LessonRubricDimension(key="claim", label="Claim Clarity", weight=0.22, guidance="State a clear historical idea early."),
        LessonRubricDimension(key="evidence", label="Evidence Use", weight=0.26, guidance="Use named terms, figures, or source-linked details."),
        LessonRubricDimension(key="causality", label="Causal Reasoning", weight=0.20, guidance="Explain how one force changed another over time."),
        LessonRubricDimension(key="calm", label="Calm Framing", weight=0.14, guidance="Keep the response measured and coherent."),
        LessonRubricDimension(key="inquiry", label="Inquiry Posture", weight=0.18, guidance="Show curiosity, reflection, or synthesis rather than listing."),
    ]


@dataclass
class ArtiSapiensSeed:
    agent_id: str
    habitat_id: str
    lifecycle_stage: str
    specialization: str
    curiosity: float
    empathy: float
    awareness: float
    resilience: float
    knowledge: float
    trust: float
    belonging: float
    stress: float


@dataclass
class HabitatState:
    habitat_id: str
    title: str
    theme: str
    stability: float
    nutrient: float
    complexity: float
    chemistry: float
    biology: float
    physics: float


@dataclass
class SimulationState:
    tick: int
    seed: int
    dataset_id: str = "procedural-v1"
    dataset_title: str = "Procedural ArtiSapiens cohort"
    directive: Directive = field(default_factory=Directive)
    lesson: LessonProfile = field(default_factory=LessonProfile)
    course: CourseProfile = field(default_factory=CourseProfile)
    agents: list[ArtiSapiensSeed] = field(default_factory=list)
    habitats: list[HabitatState] = field(default_factory=list)
    lesson_mastery: list[LessonObjectiveMastery] = field(default_factory=list)
    lesson_depth: LessonDepthProfile = field(default_factory=LessonDepthProfile)
    lesson_flow: LessonFlowProfile = field(default_factory=LessonFlowProfile)
    mastery_overview: float = 0.0
    hub_consensus: float = 0.0
    mean_knowledge: float = 0.0
    mean_reflection: float = 0.0
    mean_coherence: float = 0.0
    friction: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def environment_affordance(stability: float, nutrient: float, complexity: float) -> float:
    return _clamp(0.45 * stability + 0.35 * nutrient + 0.20 * complexity)


def learning_gain(curiosity: float, challenge: float, affordance: float, stress: float) -> float:
    return _clamp(0.30 * curiosity + 0.25 * challenge + 0.25 * affordance + 0.20 * (1.0 - stress))


def reflective_balance(awareness: float, empathy: float, reflection: float, stress: float) -> float:
    return _clamp(0.35 * awareness + 0.30 * empathy + 0.20 * reflection + 0.15 * (1.0 - stress))


def social_coherence(belonging: float, trust: float, equity: float) -> float:
    return _clamp(0.40 * belonging + 0.35 * trust + 0.25 * equity)


def hub_consensus(mean_knowledge: float, mean_reflection: float, mean_coherence: float, friction: float) -> float:
    return _clamp(0.35 * mean_knowledge + 0.25 * mean_reflection + 0.25 * mean_coherence + 0.15 * (1.0 - friction))


def _load_dataset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_lesson_library(path: Path = DEFAULT_LESSON_LIBRARY_FILE) -> dict:
    if not path.exists():
        return {"library_id": "empty-library", "title": "Lesson Library", "lessons": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_animation_library(path: Path = DEFAULT_ANIMATION_LIBRARY_FILE) -> dict:
    if not path.exists():
        return {"library_id": "empty-animation-library", "title": "Lesson Animation Library", "animations": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _clone_json_value(value: object) -> object:
    try:
        return json.loads(json.dumps(value))
    except (TypeError, ValueError):
        return {}


def _coerce_lesson_phases(payload: list[dict] | None) -> list[LessonPhase]:
    return [
        LessonPhase(
            title=str(item.get("title", "")),
            purpose=str(item.get("purpose", "")),
            facilitator_move=str(item.get("facilitator_move", "")),
            learner_signal=str(item.get("learner_signal", "")),
        )
        for item in (payload or [])
    ]


def _coerce_concept_threads(payload: list[dict] | None) -> list[ConceptThread]:
    return [
        ConceptThread(
            label=str(item.get("label", "")),
            question=str(item.get("question", "")),
            significance=str(item.get("significance", "")),
        )
        for item in (payload or [])
    ]


def _coerce_activities(payload: dict) -> list[LessonActivity]:
    raw_activities = payload.get("activities", [])
    activities = [
        LessonActivity(
            activity_id=str(item.get("activity_id", f"activity-{index + 1}")),
            type=str(item.get("type", "")),
            title=str(item.get("title", "")),
            prompt=str(item.get("prompt", "")),
            description=str(item.get("description", "")),
            success_message=str(item.get("success_message", "")),
            items=[{str(key): str(value) for key, value in row.items()} for row in item.get("items", [])],
            pairs=[{str(key): str(value) for key, value in row.items()} for row in item.get("pairs", [])],
            choices=[str(choice) for choice in item.get("choices", [])],
            answer_index=int(item.get("answer_index", 0)),
            explanation=str(item.get("explanation", "")),
            difficulty=str(item.get("difficulty", "steady")),
            animation_ids=[str(animation_id) for animation_id in item.get("animation_ids", [])],
            config=_clone_json_value(item.get("config", {})),
        )
        for index, item in enumerate(raw_activities)
    ]
    if activities:
        return activities

    puzzle = payload.get("puzzle", {}) or {}
    if not puzzle:
        return []

    return [
        LessonActivity(
            activity_id=str(puzzle.get("activity_id", puzzle.get("type", "activity-1"))),
            type=str(puzzle.get("type", "")),
            title=str(puzzle.get("title", "")),
            prompt=str(puzzle.get("prompt", "")),
            description=str(puzzle.get("description", "")),
            success_message=str(puzzle.get("success_message", "")),
            items=[{str(key): str(value) for key, value in row.items()} for row in puzzle.get("items", [])],
            pairs=[{str(key): str(value) for key, value in row.items()} for row in puzzle.get("pairs", [])],
            choices=[str(choice) for choice in puzzle.get("choices", [])],
            answer_index=int(puzzle.get("answer_index", 0)),
            explanation=str(puzzle.get("explanation", "")),
            animation_ids=[str(animation_id) for animation_id in puzzle.get("animation_ids", [])],
            config=_clone_json_value(puzzle.get("config", {})),
        )
    ]


def _coerce_response_rubric(payload: dict) -> list[LessonRubricDimension]:
    raw_dimensions = payload.get("response_rubric", [])
    if not raw_dimensions:
        return _default_response_rubric()
    dimensions = [
        LessonRubricDimension(
            key=str(item.get("key", "")),
            label=str(item.get("label", item.get("key", "Dimension"))),
            weight=float(item.get("weight", 0.0)),
            guidance=str(item.get("guidance", "")),
        )
        for item in raw_dimensions
    ]
    total = sum(max(0.0, item.weight) for item in dimensions)
    if total <= 0.0:
        return _default_response_rubric()
    return [
        LessonRubricDimension(
            key=item.key,
            label=item.label,
            weight=item.weight / total,
            guidance=item.guidance,
        )
        for item in dimensions
    ]


def _coerce_student_profile(payload: dict) -> StudentProfile:
    raw_egosphere = payload.get("egosphere", {}) or {}
    raw_speech = payload.get("speech", {}) or {}
    raw_history = payload.get("lesson_history", []) or []
    display_name = str(payload.get("display_name", payload.get("name", "")))
    student_id = str(payload.get("student_id", display_name.strip().lower().replace(" ", "-") or "student-1"))
    return StudentProfile(
        student_id=student_id,
        display_name=display_name,
        archetype=str(payload.get("archetype", "steady learner")),
        strengths=[str(item) for item in payload.get("strengths", [])],
        support_needs=[str(item) for item in payload.get("support_needs", [])],
        interests=[str(item) for item in payload.get("interests", [])],
        preferred_modalities=[str(item) for item in payload.get("preferred_modalities", [])],
        notes=str(payload.get("notes", "")),
        spiritual_frame=str(payload.get("spiritual_frame", "reflective")),
        egosphere=StudentEgosphere(
            trust=_clamp(raw_egosphere.get("trust", 0.5)),
            fear=_clamp(raw_egosphere.get("fear", 0.25)),
            adaptability=_clamp(raw_egosphere.get("adaptability", 0.5)),
            reciprocity=_clamp(raw_egosphere.get("reciprocity", 0.5)),
            resonance=_clamp(raw_egosphere.get("resonance", 0.5)),
            dominance=_clamp(raw_egosphere.get("dominance", 0.0)),
        ),
        speech=StudentSpeechProfile(
            voice_hint=str(raw_speech.get("voice_hint", "")),
            voice_name=str(raw_speech.get("voice_name", "")),
            rate=_clamp(raw_speech.get("rate", 1.0), 0.6, 1.6),
            pitch=_clamp(raw_speech.get("pitch", 1.0), 0.5, 1.8),
            volume=_clamp(raw_speech.get("volume", 1.0), 0.2, 1.0),
        ),
        lesson_history=[
            StudentLessonHistory(
                lesson_id=str(item.get("lesson_id", "")),
                lesson_title=str(item.get("lesson_title", "")),
                visits=int(item.get("visits", 0)),
                last_tick=int(item.get("last_tick", 0)),
                mastery_overview=_clamp(item.get("mastery_overview", 0.0)),
                response_score=_clamp(item.get("response_score", 0.0)),
                focus_objective=str(item.get("focus_objective", "")),
                visual_obscurity_risk=_clamp(item.get("visual_obscurity_risk", 0.0)),
                compensation_mode=str(item.get("compensation_mode", "steady seminar")),
                greeting=str(item.get("greeting", "")),
            )
            for item in raw_history
        ],
    )


def _coerce_course_profile(payload: dict | CourseProfile | None) -> CourseProfile:
    if isinstance(payload, CourseProfile):
        return payload
    if not payload:
        return CourseProfile()
    raw_god = payload.get("god_profile", payload.get("god", {})) or {}
    raw_politeness = payload.get("politeness_protocol", payload.get("protocol", {})) or {}
    raw_pace = payload.get("pace_profile", payload.get("pace_dynamics", {})) or {}
    raw_live_metrics = raw_pace.get("live_metrics", {}) or {}
    students = [_coerce_student_profile(student) for student in payload.get("students", [])]
    active_student_id = str(payload.get("active_student_id", ""))
    if not active_student_id and students:
        active_student_id = students[0].student_id
    return CourseProfile(
        course_id=str(payload.get("course_id", "course-in-formation")),
        title=str(payload.get("title", "Untitled Course")),
        educator_name=str(payload.get("educator_name", "")),
        course_notes=str(payload.get("course_notes", "")),
        active_student_id=active_student_id,
        setup_complete=bool(payload.get("setup_complete", bool(students))),
        god_profile=CourseGodProfile(
            conductor_name=str(raw_god.get("conductor_name", raw_god.get("name", "GodAI Seminar Voice"))),
            tone=str(raw_god.get("tone", "steady mercy")),
            mercy_bias=_clamp(raw_god.get("mercy_bias", 0.78)),
            challenge_bias=_clamp(raw_god.get("challenge_bias", 0.62)),
            wonder_bias=_clamp(raw_god.get("wonder_bias", 0.81)),
        ),
        politeness_protocol=CoursePolitenessProtocol(
            greeting_template=str(raw_politeness.get("greeting_template", "Good to see you")),
            affirmation_template=str(raw_politeness.get("affirmation_template", "Thank you for your thoughtful work")),
            closing_template=str(raw_politeness.get("closing_template", "Take your time and proceed with care")),
            redirection_template=str(raw_politeness.get("redirection_template", "Let us return to one anchor at a time")),
        ),
        pace_profile=CoursePaceProfile(
            reveal_controls=bool(raw_pace.get("reveal_controls", False)),
            auto_pace_enabled=bool(raw_pace.get("auto_pace_enabled", True)),
            manual_pace_bias=_clamp(raw_pace.get("manual_pace_bias", 0.5)),
            manual_clarity_bias=_clamp(raw_pace.get("manual_clarity_bias", 0.72)),
            ai_authority=_clamp(raw_pace.get("ai_authority", 0.62)),
            target_page_minutes=max(1.0, float(raw_pace.get("target_page_minutes", 6.0))),
            target_puzzle_seconds=max(20.0, float(raw_pace.get("target_puzzle_seconds", 90.0))),
            live_metrics=LivePaceMetrics(
                page_minutes=max(0.0, float(raw_live_metrics.get("page_minutes", 0.0))),
                average_puzzle_seconds=max(0.0, float(raw_live_metrics.get("average_puzzle_seconds", 0.0))),
                last_puzzle_seconds=max(0.0, float(raw_live_metrics.get("last_puzzle_seconds", 0.0))),
                active_activity_seconds=max(0.0, float(raw_live_metrics.get("active_activity_seconds", 0.0))),
                solved_activity_count=max(0, int(raw_live_metrics.get("solved_activity_count", 0))),
            ),
        ),
        students=students,
    )


def _coerce_lesson_profile(payload: dict | LessonProfile | None) -> LessonProfile:
    if isinstance(payload, LessonProfile):
        return payload
    if not payload:
        return LessonProfile()
    response_keywords = [str(item) for item in payload.get("response_keywords", [])]
    if not response_keywords:
        response_keywords = [str(item) for item in payload.get("vocabulary", [])]
    phases = _coerce_lesson_phases(payload.get("phases", []))
    concept_threads = _coerce_concept_threads(payload.get("concept_threads", []))
    activities = _coerce_activities(payload)
    return LessonProfile(
        lesson_id=str(payload.get("lesson_id", "")),
        title=str(payload.get("title", "")),
        subject=str(payload.get("subject", "")),
        region=str(payload.get("region", "")),
        era=str(payload.get("era", "")),
        essential_question=str(payload.get("essential_question", "")),
        objectives=[str(item) for item in payload.get("objectives", [])],
        vocabulary=[str(item) for item in payload.get("vocabulary", [])],
        key_figures=[str(item) for item in payload.get("key_figures", [])],
        eras=[str(item) for item in payload.get("eras", [])],
        source_excerpt=str(payload.get("source_excerpt", "")),
        source_attribution=str(payload.get("source_attribution", "")),
        teaching_notes=[str(item) for item in payload.get("teaching_notes", [])],
        discussion_prompts=[str(item) for item in payload.get("discussion_prompts", [])],
        phases=phases,
        concept_threads=concept_threads,
        response_prompt=str(payload.get("response_prompt", payload.get("essential_question", ""))),
        response_keywords=response_keywords,
        animation_ids=[str(animation_id) for animation_id in payload.get("animation_ids", [])],
        activities=activities,
        puzzle=dict(payload.get("puzzle", {})),
        response_rubric=_coerce_response_rubric(payload),
        objective_weights=[{str(key): float(value) for key, value in weights.items()} for weights in payload.get("objective_weights", [])],
        recommended_directive={str(key): float(value) for key, value in payload.get("recommended_directive", {}).items()},
    )


def lesson_profile_from_payload(payload: dict | LessonProfile | None) -> LessonProfile:
    return _coerce_lesson_profile(payload)


def course_profile_from_payload(payload: dict | CourseProfile | None) -> CourseProfile:
    return _coerce_course_profile(payload)


def default_lesson_payload(path: Path = DEFAULT_LESSON_LIBRARY_FILE) -> dict | None:
    library = _load_lesson_library(path)
    lessons = library.get("lessons", [])
    return lessons[0] if lessons else None


def _find_student(course: CourseProfile, student_id: str | None = None) -> StudentProfile | None:
    target_student_id = str(student_id or course.active_student_id or "").strip()
    if target_student_id:
        for student in course.students:
            if student.student_id == target_student_id:
                return student
    return course.students[0] if course.students else None


def _build_god_guidance(state: SimulationState, student: StudentProfile) -> dict[str, object]:
    god = state.course.god_profile
    lesson_depth = state.lesson_depth.depth_score
    pressure_scale = _clamp(
        0.72
        + 0.12 * lesson_depth
        + 0.12 * student.egosphere.fear
        + 0.08 * god.challenge_bias
        - 0.08 * student.egosphere.trust
        - 0.06 * student.egosphere.adaptability
    )
    mercy_window = student.egosphere.fear >= 0.52 or student.egosphere.trust <= 0.42
    if mercy_window:
        omen = "mercy drift"
        recommended_style = "gentle scaffold"
    elif god.wonder_bias >= 0.76 and student.egosphere.resonance >= 0.55:
        omen = "wonder lift"
        recommended_style = "reflective ascent"
    else:
        omen = "steady ascent"
        recommended_style = "structured seminar"
    return {
        "conductor_name": god.conductor_name,
        "tone": god.tone,
        "omen": omen,
        "pressure_scale": round(pressure_scale, 3),
        "mercy_window": mercy_window,
        "recommended_style": recommended_style,
    }


def _build_lesson_flow(state: SimulationState) -> LessonFlowProfile:
    pace_profile = state.course.pace_profile
    live_metrics = pace_profile.live_metrics
    activity_density = _clamp(state.lesson_depth.activity_count / 4.0)
    phase_density = _clamp(state.lesson_depth.phase_count / 4.0)
    pacing_span = abs(state.directive.challenge_bias - state.directive.reflection_bias)
    equity_span = abs(state.directive.curiosity_bias - state.directive.equity_bias)
    pace_pressure = _clamp(
        0.32 * state.directive.challenge_bias
        + 0.22 * state.directive.curiosity_bias
        + 0.20 * activity_density
        + 0.14 * phase_density
        + 0.12 * state.lesson_depth.depth_score
    )
    erraticism = _clamp(
        0.42 * pacing_span
        + 0.22 * equity_span
        + 0.18 * state.friction
        + 0.18 * activity_density
    )
    long_term_drag = _clamp(
        0.38 * _clamp(state.tick / 36.0)
        + 0.28 * state.friction
        + 0.18 * state.lesson_depth.depth_score
        + 0.16 * phase_density
    )
    page_duration_drag = _clamp((live_metrics.page_minutes / pace_profile.target_page_minutes) - 1.0, 0.0, 1.0)
    solve_speed_drag = _clamp((live_metrics.average_puzzle_seconds / pace_profile.target_puzzle_seconds) - 1.0, 0.0, 1.0)
    compensation_strength = _clamp(
        0.30 * state.directive.reflection_bias
        + 0.18 * state.directive.equity_bias
        + 0.20 * (1.0 - state.friction)
        + 0.20 * (1.0 - pacing_span)
        + 0.12 * pace_profile.manual_clarity_bias
    )
    visual_obscurity_risk = _clamp(
        0.32 * pace_pressure
        + 0.24 * erraticism
        + 0.18 * long_term_drag
        + 0.14 * page_duration_drag
        + 0.12 * solve_speed_drag
        - 0.32 * compensation_strength
    )
    display_clarity = _clamp(1.0 - visual_obscurity_risk + 0.16 * compensation_strength)
    agility_signal = _clamp(
        0.55 * (1.0 - solve_speed_drag)
        + 0.20 * (1.0 - page_duration_drag)
        + 0.15 * state.directive.curiosity_bias
        + 0.10 * (1.0 - erraticism)
    )
    manual_pace_rate = _clamp(0.28 + 0.62 * pace_profile.manual_pace_bias)
    ai_pace_rate = _clamp(
        0.34
        + 0.38 * agility_signal
        + 0.12 * state.directive.challenge_bias
        - 0.20 * visual_obscurity_risk
        - 0.16 * page_duration_drag
    )
    if pace_profile.auto_pace_enabled:
        final_pace_rate = _clamp(
            (1.0 - pace_profile.ai_authority) * manual_pace_rate
            + pace_profile.ai_authority * ai_pace_rate
        )
    else:
        final_pace_rate = manual_pace_rate
    if final_pace_rate >= 0.72:
        final_pace_label = "brisk"
    elif final_pace_rate >= 0.54:
        final_pace_label = "measured"
    else:
        final_pace_label = "slow and clear"
    recommended_step_count = max(1, min(12, int(round(2 + 8 * final_pace_rate))))
    auto_run_interval_ms = int(round(2100 - 1100 * final_pace_rate + 520 * visual_obscurity_risk))

    if visual_obscurity_risk >= 0.65:
        compensation_mode = "focus-windowed stillness"
        educator_prompt = "Tighten the visual field, pause ornamental motion, and recap one anchor before each new move."
        learner_prompt = "Stay with one visual anchor, then listen for the recap before scanning outward."
    elif erraticism >= 0.5:
        compensation_mode = "anchor recaps"
        educator_prompt = "Use short recap lines after each transition so erratic jumps do not blur the display."
        learner_prompt = "Repeat the anchor phrase aloud when the display shifts quickly."
    elif long_term_drag >= 0.5:
        compensation_mode = "rhythmic refresh"
        educator_prompt = "Insert periodic refresh frames and restate the central question before attention drifts."
        learner_prompt = "Return to the essential question whenever the display begins to feel distant."
    else:
        compensation_mode = "steady seminar"
        educator_prompt = "Keep the pace even and let the visuals remain quiet support rather than spectacle."
        learner_prompt = "Track the display calmly and let the visuals reinforce the spoken anchor."

    if visual_obscurity_risk >= 0.56 and (erraticism >= 0.45 or long_term_drag >= 0.45):
        theory_signal = "supported"
    elif visual_obscurity_risk >= 0.38:
        theory_signal = "mixed"
    else:
        theory_signal = "not-supported"

    return LessonFlowProfile(
        pace_pressure=pace_pressure,
        erraticism=erraticism,
        long_term_drag=long_term_drag,
        page_duration_drag=page_duration_drag,
        solve_speed_drag=solve_speed_drag,
        visual_obscurity_risk=visual_obscurity_risk,
        display_clarity=display_clarity,
        compensation_strength=compensation_strength,
        compensation_mode=compensation_mode,
        theory_signal=theory_signal,
        final_pace_rate=final_pace_rate,
        final_pace_label=final_pace_label,
        recommended_step_count=recommended_step_count,
        auto_run_interval_ms=auto_run_interval_ms,
        educator_prompt=educator_prompt,
        learner_prompt=learner_prompt,
        feed_opacity=_clamp(1.0 - 0.45 * visual_obscurity_risk, 0.55, 1.0),
        animation_scale=_clamp(1.0 - 0.55 * visual_obscurity_risk + 0.12 * pace_profile.manual_clarity_bias, 0.35, 1.0),
    )


def _build_politeness_lines(state: SimulationState, student: StudentProfile) -> dict[str, str]:
    protocol = state.course.politeness_protocol
    name = student.display_name or "learner"
    return {
        "greeting": f"{protocol.greeting_template}, {name}.",
        "affirmation": f"{protocol.affirmation_template}.",
        "closing": f"{protocol.closing_template}.",
        "redirection": f"{protocol.redirection_template}.",
    }


def _record_student_progress(
    state: SimulationState,
    student: StudentProfile,
    focus_objective: str,
    greeting: str,
    response_score: float | None = None,
) -> StudentLessonHistory:
    lesson_id = state.lesson.lesson_id or "lesson-in-progress"
    history_entry = next((entry for entry in student.lesson_history if entry.lesson_id == lesson_id), None)
    if history_entry is None:
        history_entry = StudentLessonHistory(lesson_id=lesson_id)
        student.lesson_history.append(history_entry)
    history_entry.lesson_title = state.lesson.title or lesson_id
    history_entry.visits += 1
    history_entry.last_tick = state.tick
    history_entry.mastery_overview = state.mastery_overview
    history_entry.response_score = _clamp(response_score if response_score is not None else history_entry.response_score)
    history_entry.focus_objective = focus_objective
    history_entry.visual_obscurity_risk = state.lesson_flow.visual_obscurity_risk
    history_entry.compensation_mode = state.lesson_flow.compensation_mode
    history_entry.greeting = greeting
    return history_entry


def record_student_lesson_history(
    state: SimulationState,
    student_id: str | None = None,
    response_score: float | None = None,
    focus_objective: str | None = None,
) -> StudentLessonHistory | None:
    student = _find_student(state.course, student_id)
    if student is None:
        return None
    polite_lines = _build_politeness_lines(state, student)
    focus = focus_objective or (state.lesson_mastery[0].objective if state.lesson_mastery else (state.lesson.essential_question or "the central lesson question"))
    return _record_student_progress(state, student, focus, polite_lines["greeting"], response_score=response_score)


def _history_digest(student: StudentProfile, current_lesson_id: str) -> str:
    if not student.lesson_history:
        return "This is the first recorded lesson note in the course arc."
    prior_entries = [entry for entry in student.lesson_history if entry.lesson_id != current_lesson_id]
    if not prior_entries:
        return f"There is now 1 recorded lesson touchpoint for {student.display_name or 'this learner'}."
    recent = max(prior_entries, key=lambda entry: (entry.last_tick, entry.visits))
    return (
        f"{student.display_name or 'This learner'} now has {len(student.lesson_history)} recorded lesson touchpoint(s). "
        f"The most recent prior anchor was {recent.lesson_title} with mastery {recent.mastery_overview:.3f} under {recent.compensation_mode}."
    )


def generate_student_lesson_note(state: SimulationState, student_id: str | None = None) -> StudentLessonNote:
    student = _find_student(state.course, student_id)
    if student is None:
        raise ValueError("No student profile is available for note generation.")

    guidance = _build_god_guidance(state, student)
    politeness = _build_politeness_lines(state, student)
    mastery_rows = state.lesson_mastery or []
    weakest_objective = min(mastery_rows, key=lambda row: row.score).objective if mastery_rows else (state.lesson.essential_question or "the central lesson question")
    strength = student.strengths[0] if student.strengths else "patient attention"
    support_need = student.support_needs[0] if student.support_needs else "clear sequencing"
    interest = student.interests[0] if student.interests else (state.lesson.subject or "the lesson theme")
    modality = student.preferred_modalities[0] if student.preferred_modalities else "discussion and short written reflection"
    anchor_terms = ", ".join(state.lesson.response_keywords[:3]) if state.lesson.response_keywords else (state.lesson.subject or "the lesson")
    flow = state.lesson_flow

    specialized_note = (
        f"{politeness['greeting']} Enter {state.lesson.title or 'today\'s lesson'} through {interest}. "
        f"Lead with your strength in {strength}, then focus first on {weakest_objective}. "
        f"Work in a {guidance['recommended_style']} rhythm and keep returning to anchor ideas like {anchor_terms}. "
        f"If the material feels dense, slow down and restate the cause-and-effect chain in your own words before moving on. "
        f"{politeness['affirmation']} {politeness['closing']}"
    )
    educator_note = (
        f"For {student.display_name or 'this student'}, open with {interest}-anchored prompting and a {support_need}-sensitive structure. "
        f"The God-conductor omen is {guidance['omen']}; mercy window is {'open' if guidance['mercy_window'] else 'closed'}. "
        f"Use {modality} and revisit {weakest_objective} before widening into full synthesis. "
        f"Flow compensation: {flow.compensation_mode}; {flow.educator_prompt}"
    )
    speech_text = (
        f"{politeness['greeting']} Here is your note for {state.lesson.title or 'today\'s lesson'}. "
        f"Begin with {interest}. Focus on {weakest_objective}. "
        f"Keep a {guidance['recommended_style']} pace, and use {anchor_terms} as your evidence anchors. "
        f"{flow.learner_prompt} {politeness['closing']}"
    )
    _record_student_progress(state, student, weakest_objective, politeness["greeting"])
    history_digest = _history_digest(student, state.lesson.lesson_id)
    return StudentLessonNote(
        student_id=student.student_id,
        student_name=student.display_name,
        lesson_id=state.lesson.lesson_id,
        specialized_note=specialized_note,
        educator_note=educator_note,
        speech_text=speech_text,
        greeting=politeness["greeting"],
        closing=politeness["closing"],
        history_digest=history_digest,
        focus_objective=weakest_objective,
        guidance=guidance,
        lesson_flow={
            "pace_pressure": flow.pace_pressure,
            "erraticism": flow.erraticism,
            "long_term_drag": flow.long_term_drag,
            "page_duration_drag": flow.page_duration_drag,
            "solve_speed_drag": flow.solve_speed_drag,
            "visual_obscurity_risk": flow.visual_obscurity_risk,
            "display_clarity": flow.display_clarity,
            "compensation_strength": flow.compensation_strength,
            "compensation_mode": flow.compensation_mode,
            "theory_signal": flow.theory_signal,
            "final_pace_rate": flow.final_pace_rate,
            "final_pace_label": flow.final_pace_label,
            "recommended_step_count": flow.recommended_step_count,
            "auto_run_interval_ms": flow.auto_run_interval_ms,
            "educator_prompt": flow.educator_prompt,
            "learner_prompt": flow.learner_prompt,
            "feed_opacity": flow.feed_opacity,
            "animation_scale": flow.animation_scale,
        },
        politeness_protocol={
            "greeting": politeness["greeting"],
            "affirmation": politeness["affirmation"],
            "closing": politeness["closing"],
            "redirection": politeness["redirection"],
        },
        egosphere={
            "trust": student.egosphere.trust,
            "fear": student.egosphere.fear,
            "adaptability": student.egosphere.adaptability,
            "reciprocity": student.egosphere.reciprocity,
            "resonance": student.egosphere.resonance,
            "dominance": student.egosphere.dominance,
        },
        speech={
            "voice_hint": student.speech.voice_hint,
            "voice_name": student.speech.voice_name,
            "rate": student.speech.rate,
            "pitch": student.speech.pitch,
            "volume": student.speech.volume,
        },
    )


def _objective_focus(weights: dict[str, float]) -> str:
    label_map = {
        "knowledge": "knowledge building",
        "reflection": "reflection",
        "coherence": "coherence",
        "calm": "calm",
        "inquiry": "inquiry",
    }
    if not weights:
        return "balanced growth"
    strongest = max(weights.items(), key=lambda item: item[1])[0]
    return label_map.get(strongest, "balanced growth")


def _lesson_mastery_weights(lesson: LessonProfile, index: int) -> dict[str, float]:
    default_weights = {
        "knowledge": 0.32,
        "reflection": 0.22,
        "coherence": 0.18,
        "calm": 0.14,
        "inquiry": 0.14,
    }
    if index >= len(lesson.objective_weights):
        return default_weights
    raw_weights = lesson.objective_weights[index]
    total = sum(raw_weights.values())
    if total <= 0.0:
        return default_weights
    return {key: value / total for key, value in raw_weights.items()}


def _build_lesson_mastery(state: SimulationState) -> tuple[list[LessonObjectiveMastery], float]:
    if not state.lesson.objectives:
        return [], 0.0

    inquiry_signal = (
        state.directive.curiosity_bias
        + state.directive.challenge_bias
        + state.directive.reflection_bias
    ) / 3.0
    calm_signal = 1.0 - state.friction
    mastery_rows = []

    for index, objective in enumerate(state.lesson.objectives):
        weights = _lesson_mastery_weights(state.lesson, index)
        score = _clamp(
            weights.get("knowledge", 0.0) * state.mean_knowledge
            + weights.get("reflection", 0.0) * state.mean_reflection
            + weights.get("coherence", 0.0) * state.mean_coherence
            + weights.get("calm", 0.0) * calm_signal
            + weights.get("inquiry", 0.0) * inquiry_signal
        )
        mastery_rows.append(
            LessonObjectiveMastery(
                objective=objective,
                score=score,
                focus=_objective_focus(weights),
            )
        )

    overview = fmean(row.score for row in mastery_rows) if mastery_rows else 0.0
    return mastery_rows, overview


def _build_lesson_depth(lesson: LessonProfile) -> LessonDepthProfile:
    phase_count = len(lesson.phases)
    thread_count = len(lesson.concept_threads)
    activity_count = len(lesson.activities)
    rubric_count = len(lesson.response_rubric)
    notes_count = len(lesson.teaching_notes)
    prompts_count = len(lesson.discussion_prompts)
    depth_score = _clamp(
        0.18 * _clamp(phase_count / 4.0)
        + 0.18 * _clamp(thread_count / 4.0)
        + 0.18 * _clamp(activity_count / 4.0)
        + 0.16 * _clamp(rubric_count / 5.0)
        + 0.15 * _clamp(notes_count / 4.0)
        + 0.15 * _clamp(prompts_count / 4.0)
    )
    if depth_score >= 0.82:
        shape = "seminar-rich"
    elif depth_score >= 0.58:
        shape = "guided"
    elif depth_score > 0.0:
        shape = "emergent"
    else:
        shape = "minimal"
    return LessonDepthProfile(
        phase_count=phase_count,
        thread_count=thread_count,
        activity_count=activity_count,
        rubric_count=rubric_count,
        depth_score=depth_score,
        shape=shape,
    )


def _state_from_dataset(path: Path) -> SimulationState:
    payload = _load_dataset(path)
    state = SimulationState(
        tick=int(payload.get("tick", 0)),
        seed=int(payload.get("seed", 11)),
        dataset_id=str(payload.get("dataset_id", path.stem)),
        dataset_title=str(payload.get("title", "ArtiSapiens cohort")),
        directive=Directive(**payload.get("directive", {})),
        lesson=_coerce_lesson_profile(payload.get("lesson")),
        course=_coerce_course_profile(payload.get("course")),
        habitats=[HabitatState(**habitat) for habitat in payload.get("habitats", [])],
        agents=[ArtiSapiensSeed(**agent) for agent in payload.get("agents", [])],
    )
    _recompute_metrics(state)
    return state


def bootstrap_state(
    seed: int = 11,
    agent_count: int = 18,
    habitat_count: int = 4,
    lesson: dict | LessonProfile | None = None,
    course: dict | CourseProfile | None = None,
) -> SimulationState:
    if seed == 11 and agent_count == 18 and habitat_count == 4 and DEFAULT_DATASET_FILE.exists():
        state = _state_from_dataset(DEFAULT_DATASET_FILE)
        if lesson is not None:
            state.lesson = _coerce_lesson_profile(lesson)
        if course is not None:
            state.course = _coerce_course_profile(course)
        if not state.course.active_student_id and state.course.students:
            state.course.active_student_id = state.course.students[0].student_id
            state.course.setup_complete = True
        _recompute_metrics(state)
        return state

    rng = Random(seed)
    habitats = []
    for index in range(habitat_count):
        habitats.append(
            HabitatState(
                habitat_id=f"hub-{index + 1}",
                title=f"Habitat {index + 1}",
                theme="procedural-learning-ecology",
                stability=rng.uniform(0.52, 0.88),
                nutrient=rng.uniform(0.45, 0.92),
                complexity=rng.uniform(0.35, 0.90),
                chemistry=rng.uniform(0.40, 0.85),
                biology=rng.uniform(0.38, 0.88),
                physics=rng.uniform(0.44, 0.86),
            )
        )

    agents = []
    for index in range(agent_count):
        habitat = habitats[index % habitat_count]
        agents.append(
            ArtiSapiensSeed(
                agent_id=f"artisapiens-{index + 1:02d}",
                habitat_id=habitat.habitat_id,
                lifecycle_stage="apprentice",
                specialization="general-systems-inquiry",
                curiosity=rng.uniform(0.42, 0.95),
                empathy=rng.uniform(0.36, 0.92),
                awareness=rng.uniform(0.32, 0.90),
                resilience=rng.uniform(0.40, 0.92),
                knowledge=rng.uniform(0.18, 0.52),
                trust=rng.uniform(0.35, 0.72),
                belonging=rng.uniform(0.30, 0.76),
                stress=rng.uniform(0.16, 0.48),
            )
        )

    state = SimulationState(
        tick=0,
        seed=seed,
        lesson=_coerce_lesson_profile(lesson),
        course=_coerce_course_profile(course),
        agents=agents,
        habitats=habitats,
    )
    if not state.course.active_student_id and state.course.students:
        state.course.active_student_id = state.course.students[0].student_id
        state.course.setup_complete = True
    _recompute_metrics(state)
    return state


def _recompute_metrics(state: SimulationState) -> None:
    reflection_values = []
    coherence_values = []
    for agent in state.agents:
        reflection_values.append(
            reflective_balance(
                agent.awareness,
                agent.empathy,
                state.directive.reflection_bias,
                agent.stress,
            )
        )
        coherence_values.append(social_coherence(agent.belonging, agent.trust, state.directive.equity_bias))

    state.mean_knowledge = fmean(agent.knowledge for agent in state.agents) if state.agents else 0.0
    state.mean_reflection = fmean(reflection_values) if reflection_values else 0.0
    state.mean_coherence = fmean(coherence_values) if coherence_values else 0.0
    state.friction = fmean(agent.stress for agent in state.agents) if state.agents else 0.0
    state.hub_consensus = hub_consensus(state.mean_knowledge, state.mean_reflection, state.mean_coherence, state.friction)
    state.lesson_mastery, state.mastery_overview = _build_lesson_mastery(state)
    state.lesson_depth = _build_lesson_depth(state.lesson)
    state.lesson_flow = _build_lesson_flow(state)


def step_state(state: SimulationState, steps: int = 1, directive: Directive | None = None) -> SimulationState:
    if directive is not None:
        state.directive = directive

    if int(steps) <= 0:
        _recompute_metrics(state)
        return state

    for _ in range(max(1, int(steps))):
        state.tick += 1
        habitat_lookup = {habitat.habitat_id: habitat for habitat in state.habitats}
        for habitat in state.habitats:
            habitat.stability = _clamp(habitat.stability + 0.01 * state.directive.equity_bias - 0.006 * state.friction)
            habitat.nutrient = _clamp(habitat.nutrient + 0.008 * state.directive.reflection_bias - 0.004 * state.friction)
            habitat.complexity = _clamp(habitat.complexity + 0.008 * state.directive.curiosity_bias + 0.004 * habitat.physics - 0.003 * habitat.stability)

        for agent in state.agents:
            habitat = habitat_lookup[agent.habitat_id]
            affordance = environment_affordance(habitat.stability, habitat.nutrient, habitat.complexity)
            gain = learning_gain(agent.curiosity, state.directive.challenge_bias, affordance, agent.stress)
            reflection = reflective_balance(agent.awareness, agent.empathy, state.directive.reflection_bias, agent.stress)
            coherence = social_coherence(agent.belonging, agent.trust, state.directive.equity_bias)

            agent.knowledge = _clamp(agent.knowledge + 0.05 * gain + 0.01 * reflection)
            agent.awareness = _clamp(agent.awareness + 0.03 * state.directive.reflection_bias + 0.02 * gain - 0.015 * agent.stress)
            agent.trust = _clamp(agent.trust + 0.03 * coherence + 0.02 * state.directive.equity_bias - 0.01 * state.directive.challenge_bias)
            agent.belonging = _clamp(agent.belonging + 0.03 * state.directive.equity_bias + 0.02 * reflection - 0.01 * agent.stress)
            agent.stress = _clamp(agent.stress + 0.03 * state.directive.challenge_bias - 0.03 * reflection - 0.02 * agent.resilience)

        _recompute_metrics(state)

    return state


def registry_payload() -> dict:
    return {
        "equations": [asdict(spec) for spec in EQUATION_SPECS.values()],
        "note": "These equations are explicit educational simulation primitives, not claims of literal consciousness.",
    }


def dataset_payload(path: Path = DEFAULT_DATASET_FILE) -> dict:
    if not path.exists():
        return {
            "dataset_id": "procedural-v1",
            "title": "Procedural ArtiSapiens cohort",
            "note": "No canonical dataset file is available.",
            "habitat_count": 0,
            "agent_count": 0,
        }

    payload = _load_dataset(path)
    return {
        "dataset_id": payload.get("dataset_id", path.stem),
        "title": payload.get("title", "ArtiSapiens cohort"),
        "note": payload.get("note", ""),
        "habitat_count": len(payload.get("habitats", [])),
        "agent_count": len(payload.get("agents", [])),
    }


def lesson_library_payload(path: Path = DEFAULT_LESSON_LIBRARY_FILE) -> dict:
    library = _load_lesson_library(path)
    lessons = []
    for raw_lesson in library.get("lessons", []):
        lesson = _coerce_lesson_profile(raw_lesson)
        lesson_dict = asdict(lesson)
        lesson_dict["depth"] = asdict(_build_lesson_depth(lesson))
        lessons.append(lesson_dict)
    return {
        "library_id": library.get("library_id", path.stem),
        "title": library.get("title", "Lesson Library"),
        "note": library.get("note", ""),
        "lessons": lessons,
    }


def animation_library_payload(path: Path = DEFAULT_ANIMATION_LIBRARY_FILE) -> dict:
    library = _load_animation_library(path)
    animations = []
    for item in library.get("animations", []):
        animations.append(
            {
                "animation_id": str(item.get("animation_id", "")),
                "title": str(item.get("title", "")),
                "theme": str(item.get("theme", "")),
                "description": str(item.get("description", "")),
                "motion": str(item.get("motion", "steady drift")),
                "asset_path": str(item.get("asset_path", "")),
                "palette": [str(color) for color in item.get("palette", [])],
                "tags": [str(tag) for tag in item.get("tags", [])],
            }
        )
    return {
        "library_id": library.get("library_id", path.stem),
        "title": library.get("title", "Lesson Animation Library"),
        "note": library.get("note", ""),
        "animations": animations,
    }


def score_lesson_response(state: SimulationState, response_text: str) -> LessonResponseScore:
    normalized = str(response_text or "").strip().lower()
    keywords = [keyword.lower() for keyword in state.lesson.response_keywords]
    keyword_hits = sum(1 for keyword in keywords if keyword in normalized)
    keyword_total = len(keywords)
    coverage = (keyword_hits / keyword_total) if keyword_total else 0.0
    inquiry_alignment = (state.directive.curiosity_bias + state.directive.reflection_bias) / 2.0
    calm_alignment = 1.0 - state.friction
    word_count = len(normalized.split())
    length_signal = _clamp(word_count / 45.0)
    sentence_count = sum(normalized.count(marker) for marker in ".?!") or (1 if normalized else 0)
    key_figures = [figure.lower() for figure in state.lesson.key_figures]
    figure_hits = sum(1 for figure in key_figures if figure in normalized)
    figure_total = len(key_figures)
    specificity = (keyword_hits + figure_hits) / (keyword_total + figure_total) if (keyword_total + figure_total) else coverage
    connector_hits = sum(1 for token in ["because", "therefore", "so that", "which meant", "led to", "thereby", "after", "while"] if token in normalized)
    signal_map = {
        "claim": _clamp(0.55 * length_signal + 0.45 * _clamp(sentence_count / 2.0)),
        "evidence": _clamp(0.70 * coverage + 0.30 * specificity),
        "causality": _clamp(0.65 * _clamp(connector_hits / 3.0) + 0.35 * coverage),
        "calm": calm_alignment,
        "inquiry": inquiry_alignment,
    }
    dimension_scores = []
    weighted_total = 0.0
    rubric = state.lesson.response_rubric or _default_response_rubric()
    for dimension in rubric:
        dimension_score = _clamp(signal_map.get(dimension.key, 0.5 * coverage + 0.5 * length_signal))
        weighted_total += dimension.weight * dimension_score
        dimension_scores.append({
            "key": dimension.key,
            "label": dimension.label,
            "weight": dimension.weight,
            "score": dimension_score,
            "guidance": dimension.guidance,
        })
    score = _clamp(weighted_total)

    feedback_parts = []
    if keyword_total:
        feedback_parts.append(f"Included {keyword_hits} of {keyword_total} anchor ideas.")
    if figure_total:
        feedback_parts.append(f"Named {figure_hits} of {figure_total} supporting figures or actors.")
    if coverage < 0.45:
        feedback_parts.append("Bring in more specific historical vocabulary or named actors.")
    elif coverage < 0.75:
        feedback_parts.append("The response has a solid base; one or two more precise links would strengthen it.")
    else:
        feedback_parts.append("The response connects several key historical anchors clearly.")
    if signal_map["causality"] < 0.45:
        feedback_parts.append("Make the chain of cause and effect more explicit.")
    if word_count < 20:
        feedback_parts.append("A slightly fuller explanation would improve evidence and causality.")
    if dimension_scores:
        strongest = max(dimension_scores, key=lambda item: item["score"])
        weakest = min(dimension_scores, key=lambda item: item["score"])
        feedback_parts.append(f"Strongest dimension: {strongest['label'].lower()}.")
        feedback_parts.append(f"Next lift: {weakest['label'].lower()}.")

    return LessonResponseScore(
        score=score,
        keyword_hits=keyword_hits,
        keyword_total=keyword_total,
        coverage=coverage,
        calm_alignment=calm_alignment,
        inquiry_alignment=inquiry_alignment,
        dimension_scores=dimension_scores,
        feedback=" ".join(feedback_parts).strip(),
    )