package com.driptech.pocode.campaign

import kotlin.math.max

object CampaignGenerator {
    fun build(request: ProjectRequest): CampaignBlueprint {
        val compiled = ProjectCompiler.compile(request)
        val nodes = buildSeededMap(request, compiled.lessons)
        return CampaignBlueprint(
            request = request,
            features = compiled.features,
            concepts = compiled.concepts,
            nodes = nodes,
            lessons = compiled.lessons.associateBy { it.id },
            adaptiveRules = AdaptiveRules(
                pacingRule = "Later lessons compress explanation windows and move faster after strong accuracy.",
                intricacyRule = "Each act combines more concepts per round and shifts from direct recall to synthesis.",
                obscuringRule = "Matching and identification games become more cryptic by using plausible distractors and indirect descriptions.",
                restRule = "Hot baths and lounge stops temporarily soften timer pressure and ambiguity for the next 2-3 lessons.",
            ),
            avatarState = AvatarState(
                moodLabel = "Curious",
                comfort = 64,
                timeSense = 58,
                recoveryBuffDescription = "Hot baths grant temporary pacing laxation.",
                inventory = listOf("CRT Cap", "Bubble Cursor", "Pixel Sneakers"),
            ),
            compilerSummary = compiled.compilerSummary,
        )
    }

    fun lessonInstanceFor(blueprint: CampaignBlueprint, node: CampaignNode, progress: PlayerProgress): LessonInstance? {
        val lessonId = node.lessonId ?: return null
        val lesson = blueprint.lessons[lessonId] ?: return null
        return AdaptiveLearningEngine.materializeLesson(lesson, progress)
    }

    fun registerLessonOutcome(progress: PlayerProgress, lessonInstance: LessonInstance, success: Boolean): PlayerProgress {
        return AdaptiveLearningEngine.registerLessonOutcome(progress, lessonInstance, success)
    }

    fun applyRestStop(progress: PlayerProgress, node: CampaignNode): PlayerProgress {
        if (node.kind != NodeKind.RestStop) {
            return progress
        }
        val relief = when (node.restStopType) {
            RestStopType.HotBath -> 3
            RestStopType.CRTLounge -> 2
            RestStopType.ArcadeBreak -> 1
            RestStopType.WardrobeKiosk -> 0
            null -> 0
        }
        return progress.copy(activeRestReliefNodes = max(progress.activeRestReliefNodes, relief))
    }

    private fun buildSeededMap(request: ProjectRequest, lessons: List<LessonBlueprint>): List<CampaignNode> {
        val seed = stableSeed(request)
        val restTypes = RestStopType.entries
        val nodes = mutableListOf<CampaignNode>()

        lessons.forEachIndexed { index, lesson ->
            val progress = (index + 1).toFloat() / lessons.size.toFloat()
            val isBoss = index == lessons.lastIndex || ((index + 1) % 4 == 0)
            nodes += CampaignNode(
                id = "lesson_$index",
                kind = if (isBoss) NodeKind.BossLesson else NodeKind.Lesson,
                title = if (isBoss) "Boss Lesson: ${lesson.title}" else lesson.title,
                subtitle = lessonSubtitle(progress),
                lessonId = lesson.id,
                lessonConcept = lesson.conceptIds.joinToString(),
                pacingDelta = lesson.basePacing,
                intricacyDelta = lesson.baseIntricacy,
                obscurityDelta = lesson.baseObscurity,
            )

            val shouldInsertRest = lessons.size >= 7 && index < lessons.lastIndex && ((seed + index) % 3 == 0)
            if (shouldInsertRest) {
                val restType = restTypes[(seed + index).mod(restTypes.size)]
                nodes += CampaignNode(
                    id = "rest_$index",
                    kind = NodeKind.RestStop,
                    title = restTitle(restType),
                    subtitle = restSubtitle(restType),
                    restStopType = restType,
                    pacingDelta = -0.18f,
                    intricacyDelta = -0.08f,
                    obscurityDelta = -0.12f,
                )
            }

            val shouldInsertReward = index < lessons.lastIndex && ((seed + index) % 5 == 0)
            if (shouldInsertReward) {
                nodes += CampaignNode(
                    id = "reward_$index",
                    kind = NodeKind.RewardCache,
                    title = "Floppy Cache",
                    subtitle = "Avatar reward drop and theme loot.",
                )
            }
        }

        return nodes
    }

    private fun stableSeed(request: ProjectRequest): Int {
        return max(1, (request.seedWord + request.projectIdea + request.language).uppercase().fold(7) { acc, c -> (acc * 31) + c.code })
    }

    private fun lessonSubtitle(progress: Float): String {
        return when {
            progress < 0.34f -> "Direct clue phase. Fast comprehension with low ambiguity."
            progress < 0.68f -> "Mixed concept phase. Distractors get closer to correct behavior."
            else -> "Cryptic phase. Inference, pattern recognition, and tighter pacing dominate."
        }
    }

    private fun restTitle(type: RestStopType): String = when (type) {
        RestStopType.HotBath -> "Hot Bath Stop"
        RestStopType.WardrobeKiosk -> "Wardrobe Kiosk"
        RestStopType.ArcadeBreak -> "Arcade Break"
        RestStopType.CRTLounge -> "CRT Lounge"
    }

    private fun restSubtitle(type: RestStopType): String = when (type) {
        RestStopType.HotBath -> "Avatar relaxes and gains a temporary timing buffer for upcoming lessons."
        RestStopType.WardrobeKiosk -> "Equip new cosmetics and keep the route stylish."
        RestStopType.ArcadeBreak -> "Short diversion with a small pattern-recognition bonus."
        RestStopType.CRTLounge -> "Future lesson pressure becomes easier to read for a short span."
    }
}