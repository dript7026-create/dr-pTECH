package com.driptech.pocode.campaign

data class ProjectRequest(
    val projectIdea: String,
    val language: String,
    val learnerLevel: String,
    val sessionLengthMinutes: Int,
    val seedWord: String,
)

data class FeatureIntent(
    val id: String,
    val title: String,
    val summary: String,
)

data class ConceptUnit(
    val id: String,
    val title: String,
    val summary: String,
)

enum class MiniGameType {
    Identify,
    Match,
    Repair,
    Assemble,
    Predict,
}

data class MiniGamePrompt(
    val id: String,
    val type: MiniGameType,
    val prompt: String,
    val options: List<String>,
    val correctAnswer: String,
    val hint: String,
    val obscurityTier: Int,
    val primaryConceptId: String,
    val reinforcement: Boolean = false,
)

data class LessonBlueprint(
    val id: String,
    val title: String,
    val subtitle: String,
    val conceptIds: List<String>,
    val games: List<MiniGamePrompt>,
    val basePacing: Float,
    val baseIntricacy: Float,
    val baseObscurity: Float,
)

data class LessonInstance(
    val lesson: LessonBlueprint,
    val games: List<MiniGamePrompt>,
    val pacingHint: String,
    val remediationSummary: String,
)

enum class NodeKind {
    Lesson,
    BossLesson,
    RestStop,
    RewardCache,
}

enum class RestStopType {
    HotBath,
    WardrobeKiosk,
    ArcadeBreak,
    CRTLounge,
}

data class CampaignNode(
    val id: String,
    val kind: NodeKind,
    val title: String,
    val subtitle: String,
    val lessonId: String? = null,
    val lessonConcept: String? = null,
    val restStopType: RestStopType? = null,
    val pacingDelta: Float = 0f,
    val intricacyDelta: Float = 0f,
    val obscurityDelta: Float = 0f,
)

data class AdaptiveRules(
    val pacingRule: String,
    val intricacyRule: String,
    val obscuringRule: String,
    val restRule: String,
)

data class AvatarState(
    val moodLabel: String,
    val comfort: Int,
    val timeSense: Int,
    val recoveryBuffDescription: String,
    val inventory: List<String> = emptyList(),
)

data class PlayerProgress(
    val completedLessonIds: Set<String> = emptySet(),
    val totalSuccesses: Int = 0,
    val totalMistakes: Int = 0,
    val recentAccuracy: Float = 0.72f,
    val conceptMistakes: Map<String, Int> = emptyMap(),
    val activeRestReliefNodes: Int = 0,
    val avatarInventory: List<String> = listOf("CRT Cap", "Starter Jacket"),
)

data class GameResult(
    val gameId: String,
    val conceptId: String,
    val correct: Boolean,
    val chosenAnswer: String,
)

data class LessonResult(
    val lessonId: String,
    val results: List<GameResult>,
) {
    val correctCount get() = results.count { it.correct }
    val totalCount get() = results.size
    val accuracy get() = if (totalCount > 0) correctCount.toFloat() / totalCount else 0f
    val passed get() = accuracy >= 0.6f
}

data class CampaignBlueprint(
    val request: ProjectRequest,
    val features: List<FeatureIntent>,
    val concepts: List<ConceptUnit>,
    val nodes: List<CampaignNode>,
    val lessons: Map<String, LessonBlueprint>,
    val adaptiveRules: AdaptiveRules,
    val avatarState: AvatarState,
    val compilerSummary: String,
)