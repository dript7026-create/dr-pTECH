package com.driptech.pocode.campaign

object AdaptiveLearningEngine {
    fun materializeLesson(lesson: LessonBlueprint, progress: PlayerProgress): LessonInstance {
        val repeatedConcepts = lesson.conceptIds.filter { conceptId -> (progress.conceptMistakes[conceptId] ?: 0) > 0 }
        val remediationGames = repeatedConcepts.flatMapIndexed { index, conceptId ->
            listOf(
                MiniGamePrompt(
                    id = "${lesson.id}_remediate_identify_$index",
                    type = MiniGameType.Identify,
                    prompt = "Try '${conceptId}' again with a more direct clue.",
                    options = listOf(
                        "Choose the answer that keeps the project feature stable.",
                        "Choose the answer that removes state and feedback.",
                        "Choose the answer that breaks the user flow.",
                    ),
                    correctAnswer = "Choose the answer that keeps the project feature stable.",
                    hint = "Mistakes add another learning opportunity rather than ending the run.",
                    obscurityTier = 1,
                    primaryConceptId = conceptId,
                    reinforcement = true,
                ),
                MiniGamePrompt(
                    id = "${lesson.id}_remediate_match_$index",
                    type = MiniGameType.Match,
                    prompt = "Re-match the project behavior for '${conceptId}' before moving on.",
                    options = listOf(
                        "Select the behavior that preserves useful project logic.",
                        "Select the behavior that erases the result.",
                        "Select the behavior that dodges validation.",
                    ),
                    correctAnswer = "Select the behavior that preserves useful project logic.",
                    hint = "Repeated opportunities should answer the exact weakness the player showed.",
                    obscurityTier = 1,
                    primaryConceptId = conceptId,
                    reinforcement = true,
                ),
            )
        }

        val adjustedObscurityDrop = if (progress.activeRestReliefNodes > 0) 1 else 0
        val adjustedGames = lesson.games.map { prompt ->
            val newTier = (prompt.obscurityTier - adjustedObscurityDrop).coerceAtLeast(1)
            if (progress.recentAccuracy > 0.86f && progress.activeRestReliefNodes == 0) {
                prompt.copy(
                    obscurityTier = (newTier + 1).coerceAtMost(4),
                    hint = "Infer from structure, state flow, and result shape."
                )
            } else {
                prompt.copy(obscurityTier = newTier)
            }
        }

        val paceSummary = when {
            progress.activeRestReliefNodes > 0 -> "Rest relief active: pacing softened for the next few nodes."
            progress.recentAccuracy > 0.86f -> "Mastery momentum active: pacing accelerates and hints shrink."
            progress.totalMistakes > progress.totalSuccesses -> "Recovery mode active: more direct guidance and reinforcement loops added."
            else -> "Baseline pace active: steady pressure with rising intricacy."
        }

        val remediationSummary = if (remediationGames.isEmpty()) {
            "No remediation loops inserted for this lesson."
        } else {
            "Inserted ${remediationGames.size} reinforcement games to address recent mistakes."
        }

        return LessonInstance(
            lesson = lesson,
            games = adjustedGames + remediationGames,
            pacingHint = paceSummary,
            remediationSummary = remediationSummary,
        )
    }

    fun registerLessonOutcome(progress: PlayerProgress, lessonInstance: LessonInstance, success: Boolean): PlayerProgress {
        return if (success) {
            progress.copy(
                completedLessonIds = progress.completedLessonIds + lessonInstance.lesson.id,
                totalSuccesses = progress.totalSuccesses + 1,
                recentAccuracy = ((progress.recentAccuracy * 3f) + 1f) / 4f,
                activeRestReliefNodes = (progress.activeRestReliefNodes - 1).coerceAtLeast(0),
            )
        } else {
            val updatedConceptMistakes = progress.conceptMistakes.toMutableMap()
            lessonInstance.lesson.conceptIds.forEach { conceptId ->
                updatedConceptMistakes[conceptId] = (updatedConceptMistakes[conceptId] ?: 0) + 1
            }
            progress.copy(
                totalMistakes = progress.totalMistakes + 1,
                recentAccuracy = (progress.recentAccuracy * 3f) / 4f,
                conceptMistakes = updatedConceptMistakes,
                activeRestReliefNodes = (progress.activeRestReliefNodes - 1).coerceAtLeast(0),
            )
        }
    }

    fun registerDetailedOutcome(progress: PlayerProgress, result: LessonResult): PlayerProgress {
        val updatedConceptMistakes = progress.conceptMistakes.toMutableMap()
        result.results.filter { !it.correct }.forEach { gameResult ->
            updatedConceptMistakes[gameResult.conceptId] = (updatedConceptMistakes[gameResult.conceptId] ?: 0) + 1
        }
        val lessonAccuracy = result.accuracy
        val newAccuracy = ((progress.recentAccuracy * 3f) + lessonAccuracy) / 4f
        return if (result.passed) {
            progress.copy(
                completedLessonIds = progress.completedLessonIds + result.lessonId,
                totalSuccesses = progress.totalSuccesses + result.correctCount,
                totalMistakes = progress.totalMistakes + (result.totalCount - result.correctCount),
                recentAccuracy = newAccuracy,
                conceptMistakes = updatedConceptMistakes,
                activeRestReliefNodes = (progress.activeRestReliefNodes - 1).coerceAtLeast(0),
            )
        } else {
            progress.copy(
                totalSuccesses = progress.totalSuccesses + result.correctCount,
                totalMistakes = progress.totalMistakes + (result.totalCount - result.correctCount),
                recentAccuracy = newAccuracy,
                conceptMistakes = updatedConceptMistakes,
                activeRestReliefNodes = (progress.activeRestReliefNodes - 1).coerceAtLeast(0),
            )
        }
    }
}