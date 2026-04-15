package com.driptech.pocode.campaign

object ProjectCompiler {
    data class CompiledProject(
        val features: List<FeatureIntent>,
        val concepts: List<ConceptUnit>,
        val lessons: List<LessonBlueprint>,
        val compilerSummary: String,
    )

    fun compile(request: ProjectRequest): CompiledProject {
        val features = inferFeatures(request)
        val concepts = buildConceptGraph(request, features)
        val lessons = chunkConceptsIntoLessons(request, concepts)
        return CompiledProject(
            features = features,
            concepts = concepts,
            lessons = lessons,
            compilerSummary = "Parsed ${features.size} feature intents and ${concepts.size} concept units from project idea '${request.projectIdea}'.",
        )
    }

    private fun inferFeatures(request: ProjectRequest): List<FeatureIntent> {
        val normalized = request.projectIdea.lowercase()
        val features = mutableListOf(
            FeatureIntent("input", "User Input", "The project accepts player or user-provided data."),
            FeatureIntent("output", "Readable Output", "The project displays useful feedback or results."),
            FeatureIntent("rules", "Program Rules", "The project applies conditions or transformations to data."),
        )

        if ("budget" in normalized || "tracker" in normalized || "finance" in normalized) {
            features += FeatureIntent("records", "Categorized Records", "Entries need categories, totals, and review views.")
            features += FeatureIntent("storage", "Saved Ledger", "Data should persist between sessions.")
        }
        if ("todo" in normalized || "task" in normalized || "list" in normalized) {
            features += FeatureIntent("lists", "Mutable Lists", "The project manages growing and shrinking item collections.")
        }
        if ("adventure" in normalized || "story" in normalized || "game" in normalized) {
            features += FeatureIntent("state", "Scene State", "The project needs progression state and branches.")
            features += FeatureIntent("looping", "Interaction Loop", "The project repeats actions until exit or completion.")
        }
        if ("score" in normalized || "reward" in normalized || "level" in normalized) {
            features += FeatureIntent("progression", "Progress Tracking", "The project needs milestones, scores, or unlock state.")
        }
        if (
            "text to speech" in normalized ||
            "tts" in normalized ||
            "speech" in normalized ||
            ("text" in normalized && "voice" in normalized)
        ) {
            features += FeatureIntent("text_processing", "Text Processing", "The project prepares raw text for clean spoken output.")
            features += FeatureIntent("speech_output", "Speech Synthesis Output", "The project converts text into spoken audio using a platform voice layer.")
            features += FeatureIntent("voice_settings", "Voice Settings", "The project exposes rate, pitch, or voice selection controls.")
            features += FeatureIntent("history", "Utterance History", "The project may keep recently spoken phrases or favorites.")
        }

        return features.distinctBy { it.id }
    }

    private fun buildConceptGraph(request: ProjectRequest, features: List<FeatureIntent>): List<ConceptUnit> {
        val concepts = mutableListOf(
            ConceptUnit("variables", "Variables and values", "Store named pieces of project state."),
            ConceptUnit("io", "Input and output", "Read data and return readable feedback."),
            ConceptUnit("conditions", "Conditions and branching", "Route logic depending on state and rules."),
            ConceptUnit("loops", "Loops and repeated tasks", "Repeat checks, menus, and updates."),
            ConceptUnit("functions", "Functions and reusable actions", "Break the project into named actions."),
        )

        if (features.any { it.id == "lists" || it.id == "records" }) {
            concepts += ConceptUnit("collections", "Collections and records", "Model repeated items and grouped fields.")
        }
        if (features.any { it.id == "storage" || it.id == "progression" }) {
            concepts += ConceptUnit("persistence", "Persistence and saved state", "Write and restore project data between runs.")
        }
        if (features.any { it.id == "state" }) {
            concepts += ConceptUnit("stateflow", "State flow and scene progression", "Track where the user is and what changes next.")
        }
        if (features.any { it.id == "records" }) {
            concepts += ConceptUnit("aggregation", "Categorization and totals", "Group data and compute summaries.")
        }
        if (features.any { it.id == "text_processing" }) {
            concepts += ConceptUnit("textprep", "Text cleanup and normalization", "Prepare text so punctuation, spacing, and phrasing speak clearly.")
        }
        if (features.any { it.id == "speech_output" }) {
            concepts += ConceptUnit("platform_audio", "Platform audio and speech APIs", "Trigger native or service-backed speech playback from app state.")
        }
        if (features.any { it.id == "voice_settings" }) {
            concepts += ConceptUnit("config", "Configuration and voice controls", "Apply pitch, rate, voice, and playback preferences safely.")
        }
        if (features.any { it.id == "history" }) {
            concepts += ConceptUnit("history", "History and saved phrases", "Store and retrieve recent utterances or favorites.")
        }

        concepts += ConceptUnit("debugging", "Debugging and assembly", "Fix the final build and join the pieces.")
        return concepts.distinctBy { it.id }
    }

    private fun chunkConceptsIntoLessons(request: ProjectRequest, concepts: List<ConceptUnit>): List<LessonBlueprint> {
        val lessons = mutableListOf<LessonBlueprint>()
        var cursor = 0
        while (cursor < concepts.size) {
            val lessonSize = when {
                cursor < 2 -> 1
                cursor < 5 -> 2
                else -> 2
            }
            val group = concepts.drop(cursor).take(lessonSize)
            val progress = (cursor + group.size).toFloat() / concepts.size.toFloat()
            val lessonId = "lesson_${cursor}_${group.first().id}"
            lessons += LessonBlueprint(
                id = lessonId,
                title = group.joinToString(" + ") { it.title },
                subtitle = "Build project understanding through quick, cryptic loops.",
                conceptIds = group.map { it.id },
                games = buildMiniGames(request, lessonId, group, progress),
                basePacing = 1.0f + progress * 0.6f,
                baseIntricacy = 1.0f + progress * 0.85f,
                baseObscurity = 1.0f + progress,
            )
            cursor += group.size
        }
        return lessons
    }

    private fun buildMiniGames(request: ProjectRequest, lessonId: String, concepts: List<ConceptUnit>, progress: Float): List<MiniGamePrompt> {
        if (isTextToSpeechProject(request)) {
            return buildTextToSpeechMiniGames(lessonId, concepts, progress)
        }

        val prompts = mutableListOf<MiniGamePrompt>()
        concepts.forEachIndexed { index, concept ->
            prompts += MiniGamePrompt(
                id = "${lessonId}_identify_$index",
                type = MiniGameType.Identify,
                prompt = "Which project need is this fragment addressing for '${concept.title}'?",
                options = listOf(
                    concept.summary,
                    "It only changes avatar cosmetics.",
                    "It removes all branching from the project.",
                    "It replaces saved state with random noise.",
                ),
                correctAnswer = concept.summary,
                hint = "Look for the underlying project behavior, not just the keyword.",
                obscurityTier = obscurityTier(progress),
                primaryConceptId = concept.id,
            )
            prompts += MiniGamePrompt(
                id = "${lessonId}_match_$index",
                type = MiniGameType.Match,
                prompt = "Match the code behavior to the best outcome for '${concept.title}'.",
                options = listOf(
                    "Correctly supports ${concept.title.lowercase()} in the project flow.",
                    "Only renames variables without changing behavior.",
                    "Breaks the project after one successful run.",
                    "Skips all user feedback.",
                ),
                correctAnswer = "Correctly supports ${concept.title.lowercase()} in the project flow.",
                hint = "The best answer preserves useful behavior instead of cosmetic change.",
                obscurityTier = obscurityTier(progress + 0.1f),
                primaryConceptId = concept.id,
            )
        }

        if (concepts.size > 1) {
            val combined = concepts.joinToString(" and ") { it.title.lowercase() }
            prompts += MiniGamePrompt(
                id = "${lessonId}_assemble_combo",
                type = MiniGameType.Assemble,
                prompt = "Assemble the project step that combines $combined into one working slice.",
                options = listOf(
                    "Gather input, apply rules, then return structured output.",
                    "Delete stored state before reading it.",
                    "Only rename functions without using them.",
                    "Skip validation and hope the output is correct.",
                ),
                correctAnswer = "Gather input, apply rules, then return structured output.",
                hint = "The correct step preserves flow from input to useful result.",
                obscurityTier = obscurityTier(progress + 0.2f),
                primaryConceptId = concepts.last().id,
            )
        }

        prompts += MiniGamePrompt(
            id = "${lessonId}_repair_final",
            type = MiniGameType.Repair,
            prompt = "Repair the project fragment so it survives a real user mistake.",
            options = listOf(
                "Add a guarded path with feedback and keep the main flow running.",
                "Crash immediately after invalid input.",
                "Remove the check and hide the output.",
                "Store the wrong variable on purpose.",
            ),
            correctAnswer = "Add a guarded path with feedback and keep the main flow running.",
            hint = "A good repair keeps the lesson project resilient.",
            obscurityTier = obscurityTier(progress + 0.25f),
            primaryConceptId = concepts.last().id,
        )

        return prompts
    }

    private fun buildTextToSpeechMiniGames(lessonId: String, concepts: List<ConceptUnit>, progress: Float): List<MiniGamePrompt> {
        val prompts = mutableListOf<MiniGamePrompt>()
        concepts.forEachIndexed { index, concept ->
            val identifyPrompt = when (concept.id) {
                "textprep" -> MiniGamePrompt(
                    id = "${lessonId}_identify_$index",
                    type = MiniGameType.Identify,
                    prompt = "Which preprocessing step best helps a TTS app speak a pasted paragraph clearly?",
                    options = listOf(
                        "Normalize whitespace and punctuation before sending the utterance.",
                        "Duplicate every punctuation mark to make the voice louder.",
                        "Drop all sentence boundaries so the app speaks one long blur.",
                        "Convert every word to random casing before playback.",
                    ),
                    correctAnswer = "Normalize whitespace and punctuation before sending the utterance.",
                    hint = "Good speech output starts with clean text shape.",
                    obscurityTier = obscurityTier(progress),
                    primaryConceptId = concept.id,
                )
                "platform_audio" -> MiniGamePrompt(
                    id = "${lessonId}_identify_$index",
                    type = MiniGameType.Identify,
                    prompt = "Which app action actually connects text input to spoken output?",
                    options = listOf(
                        "Pass the cleaned string into the platform speech engine.",
                        "Rename the speak button without changing the handler.",
                        "Store the text but never trigger playback.",
                        "Animate the waveform while leaving audio silent.",
                    ),
                    correctAnswer = "Pass the cleaned string into the platform speech engine.",
                    hint = "A TTS app needs a real handoff from text state to speech playback.",
                    obscurityTier = obscurityTier(progress),
                    primaryConceptId = concept.id,
                )
                "config" -> MiniGamePrompt(
                    id = "${lessonId}_identify_$index",
                    type = MiniGameType.Identify,
                    prompt = "Which setting flow best supports voice-rate and pitch controls without breaking playback?",
                    options = listOf(
                        "Validate the slider values, then apply them before speech starts.",
                        "Apply impossible values and hope the engine corrects them.",
                        "Change labels on screen but never update the real settings.",
                        "Reset playback every time the user opens the settings panel.",
                    ),
                    correctAnswer = "Validate the slider values, then apply them before speech starts.",
                    hint = "Config changes should be safe, bounded, and attached to real playback state.",
                    obscurityTier = obscurityTier(progress),
                    primaryConceptId = concept.id,
                )
                "history" -> MiniGamePrompt(
                    id = "${lessonId}_identify_$index",
                    type = MiniGameType.Identify,
                    prompt = "What makes an utterance history useful in a TTS tool?",
                    options = listOf(
                        "The app can revisit recent phrases or favorites quickly.",
                        "The app deletes every spoken phrase immediately after playback.",
                        "The app stores only button colors instead of utterances.",
                        "The app removes replay so users must retype every line.",
                    ),
                    correctAnswer = "The app can revisit recent phrases or favorites quickly.",
                    hint = "History is about fast reuse, not cosmetic change.",
                    obscurityTier = obscurityTier(progress),
                    primaryConceptId = concept.id,
                )
                else -> MiniGamePrompt(
                    id = "${lessonId}_identify_$index",
                    type = MiniGameType.Identify,
                    prompt = "Which TTS app need is this fragment addressing for '${concept.title}'?",
                    options = listOf(
                        concept.summary,
                        "It only recolors the avatar room.",
                        "It removes spoken feedback from the project.",
                        "It breaks the speech flow after one tap.",
                    ),
                    correctAnswer = concept.summary,
                    hint = "Map the fragment to speech-app behavior rather than surface wording.",
                    obscurityTier = obscurityTier(progress),
                    primaryConceptId = concept.id,
                )
            }

            val matchPrompt = MiniGamePrompt(
                id = "${lessonId}_match_$index",
                type = MiniGameType.Match,
                prompt = "Match '${concept.title}' to the best text-to-speech outcome.",
                options = listOf(
                    ttsOutcomeFor(concept.id),
                    "Playback becomes less predictable each time the user taps speak.",
                    "The phrase renders onscreen but never reaches the speech path.",
                    "The app changes visuals while leaving voice behavior broken.",
                ),
                correctAnswer = ttsOutcomeFor(concept.id),
                hint = "Pick the outcome that improves the speech pipeline end to end.",
                obscurityTier = obscurityTier(progress + 0.1f),
                primaryConceptId = concept.id,
            )

            prompts += identifyPrompt
            prompts += matchPrompt
        }

        if (concepts.size > 1) {
            prompts += MiniGamePrompt(
                id = "${lessonId}_assemble_combo",
                type = MiniGameType.Assemble,
                prompt = "Assemble the TTS pipeline slice that goes from typed phrase to spoken output.",
                options = listOf(
                    "Capture text, normalize it, apply voice settings, then trigger speech playback.",
                    "Trigger playback first, then ask for the text afterward.",
                    "Save the phrase history but never call the speech engine.",
                    "Only redraw the screen while the utterance stays unsaid.",
                ),
                correctAnswer = "Capture text, normalize it, apply voice settings, then trigger speech playback.",
                hint = "The correct order preserves the real speak flow from input to audio.",
                obscurityTier = obscurityTier(progress + 0.2f),
                primaryConceptId = concepts.last().id,
            )
        }

        prompts += MiniGamePrompt(
            id = "${lessonId}_repair_final",
            type = MiniGameType.Repair,
            prompt = "Repair the TTS app so a malformed phrase or bad setting does not break the speaking flow.",
            options = listOf(
                "Guard invalid settings, keep the phrase visible, and return clear feedback before retrying speech.",
                "Crash the playback path as soon as a bad value appears.",
                "Ignore the error and pretend the utterance was spoken.",
                "Erase the phrase history and mute the engine permanently.",
            ),
            correctAnswer = "Guard invalid settings, keep the phrase visible, and return clear feedback before retrying speech.",
            hint = "A resilient TTS app recovers visibly and keeps the user oriented.",
            obscurityTier = obscurityTier(progress + 0.25f),
            primaryConceptId = concepts.last().id,
        )

        return prompts
    }

    private fun isTextToSpeechProject(request: ProjectRequest): Boolean {
        val normalized = request.projectIdea.lowercase()
        return "text to speech" in normalized || "tts" in normalized || "speech" in normalized || ("text" in normalized && "voice" in normalized)
    }

    private fun ttsOutcomeFor(conceptId: String): String = when (conceptId) {
        "textprep" -> "The utterance sounds cleaner because the text is normalized before speech begins."
        "platform_audio" -> "The typed phrase reaches the speech engine and actually plays through the device voice layer."
        "config" -> "Playback respects the selected pitch, rate, and voice without invalid settings slipping through."
        "history" -> "The user can replay recent phrases or favorites without retyping them."
        "persistence" -> "Saved phrases and preferences survive the next app launch."
        else -> "The TTS app preserves a stable step in the phrase-to-voice pipeline."
    }

    private fun obscurityTier(progress: Float): Int {
        return when {
            progress < 0.34f -> 1
            progress < 0.68f -> 2
            progress < 0.88f -> 3
            else -> 4
        }
    }
}