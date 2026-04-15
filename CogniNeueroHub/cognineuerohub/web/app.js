const stateEls = {
  tick: document.getElementById("tick"),
  consensus: document.getElementById("consensus"),
  knowledge: document.getElementById("knowledge"),
  reflection: document.getElementById("reflection-metric"),
  coherence: document.getElementById("coherence"),
  friction: document.getElementById("friction"),
  habitats: document.getElementById("habitats"),
  cohort: document.getElementById("cohort"),
  registry: document.getElementById("registry"),
  datasetTitle: document.getElementById("dataset-title"),
  datasetNote: document.getElementById("dataset-note"),
  lessonTitle: document.getElementById("lesson-title"),
  lessonMeta: document.getElementById("lesson-meta"),
  lessonQuestion: document.getElementById("lesson-question"),
  lessonObjectives: document.getElementById("lesson-objectives"),
  lessonNotes: document.getElementById("lesson-notes"),
  lessonPhases: document.getElementById("lesson-phases"),
  lessonVocabulary: document.getElementById("lesson-vocabulary"),
  lessonFigures: document.getElementById("lesson-figures"),
  lessonAnimations: document.getElementById("lesson-animations"),
  lessonThreads: document.getElementById("lesson-threads"),
  lessonPrompts: document.getElementById("lesson-prompts"),
  lessonSource: document.getElementById("lesson-source"),
  lessonSourceAttribution: document.getElementById("lesson-source-attribution"),
  lessonEras: document.getElementById("lesson-eras"),
  lessonRubric: document.getElementById("lesson-rubric"),
  lessonDepth: document.getElementById("lesson-depth"),
  masteryOverview: document.getElementById("mastery-overview"),
  lessonLibraryNote: document.getElementById("lesson-library-note"),
  narrativeSubject: document.getElementById("narrative-subject"),
  narrativeProgress: document.getElementById("narrative-progress"),
  narrativeStage: document.getElementById("narrative-stage"),
  narrativeBody: document.getElementById("narrative-body"),
  narrativeContext: document.getElementById("narrative-context"),
  responsePrompt: document.getElementById("response-prompt"),
  responseInput: document.getElementById("response-input"),
  responseScore: document.getElementById("response-score"),
  responseFeedback: document.getElementById("response-feedback"),
  responseDimensions: document.getElementById("response-dimensions"),
  livePaceMeter: document.getElementById("live-pace-meter"),
  livePaceMeterSub: document.getElementById("live-pace-meter-sub"),
  livePaceSparklineFill: document.getElementById("live-pace-sparkline-fill"),
  livePaceSparklinePath: document.getElementById("live-pace-sparkline-path"),
  courseStatus: document.getElementById("course-status"),
  studentNoteOutput: document.getElementById("student-note-output"),
  educatorNoteOutput: document.getElementById("educator-note-output"),
  godGuidanceOutput: document.getElementById("god-guidance-output"),
  studentHistoryOutput: document.getElementById("student-history-output"),
  paceTheoryOutput: document.getElementById("pace-theory-output"),
  paceCompensationOutput: document.getElementById("pace-compensation-output"),
  paceVisualOutput: document.getElementById("pace-visual-output"),
  paceRuntimeOutput: document.getElementById("pace-runtime-output"),
  activityRail: document.getElementById("activity-rail"),
  puzzleTitle: document.getElementById("puzzle-title"),
  puzzlePrompt: document.getElementById("puzzle-prompt"),
  puzzleBoard: document.getElementById("puzzle-board"),
  puzzleFeedback: document.getElementById("puzzle-feedback"),
  puzzleAssistOutput: document.getElementById("puzzle-assist-output"),
  puzzleBranchOutput: document.getElementById("puzzle-branch-output"),
  feedFocusNote: document.getElementById("feed-focus-note"),
  authoringStatus: document.getElementById("authoring-status"),
  authoringPreview: document.getElementById("authoring-preview"),
};

const controls = {
  lessonSelect: document.getElementById("lesson-select"),
  studentSelect: document.getElementById("student-select"),
  steps: document.getElementById("steps"),
  curiosity: document.getElementById("curiosity"),
  equity: document.getElementById("equity"),
  challenge: document.getElementById("challenge"),
  reflection: document.getElementById("reflection"),
  courseTitleInput: document.getElementById("course-title-input"),
  courseEducatorInput: document.getElementById("course-educator-input"),
  courseNotesInput: document.getElementById("course-notes-input"),
  godNameInput: document.getElementById("god-name-input"),
  godToneInput: document.getElementById("god-tone-input"),
  godMercyInput: document.getElementById("god-mercy-input"),
  godChallengeInput: document.getElementById("god-challenge-input"),
  godWonderInput: document.getElementById("god-wonder-input"),
  protocolGreetingInput: document.getElementById("protocol-greeting-input"),
  protocolAffirmationInput: document.getElementById("protocol-affirmation-input"),
  protocolClosingInput: document.getElementById("protocol-closing-input"),
  protocolRedirectionInput: document.getElementById("protocol-redirection-input"),
  paceAutoEnableInput: document.getElementById("pace-auto-enable-input"),
  paceManualInput: document.getElementById("pace-manual-input"),
  paceClarityInput: document.getElementById("pace-clarity-input"),
  paceAiAuthorityInput: document.getElementById("pace-ai-authority-input"),
  pacePageTargetInput: document.getElementById("pace-page-target-input"),
  pacePuzzleTargetInput: document.getElementById("pace-puzzle-target-input"),
  authorLessonTitleInput: document.getElementById("author-lesson-title-input"),
  authorAnimationPicker: document.getElementById("author-animation-picker"),
  authorGameActivityIdInput: document.getElementById("author-game-activity-id-input"),
  authorGameTitleInput: document.getElementById("author-game-title-input"),
  authorGamePromptInput: document.getElementById("author-game-prompt-input"),
  authorGameSupportInput: document.getElementById("author-game-support-input"),
  authorGameCompletionInput: document.getElementById("author-game-completion-input"),
  authorGameTokensInput: document.getElementById("author-game-tokens-input"),
  studentNameInput: document.getElementById("student-name-input"),
  studentArchetypeInput: document.getElementById("student-archetype-input"),
  studentSpiritualFrameInput: document.getElementById("student-spiritual-frame-input"),
  studentStrengthsInput: document.getElementById("student-strengths-input"),
  studentSupportsInput: document.getElementById("student-supports-input"),
  studentInterestsInput: document.getElementById("student-interests-input"),
  studentModalitiesInput: document.getElementById("student-modalities-input"),
  studentNotesInput: document.getElementById("student-notes-input"),
  studentTrustInput: document.getElementById("student-trust-input"),
  studentFearInput: document.getElementById("student-fear-input"),
  studentAdaptabilityInput: document.getElementById("student-adaptability-input"),
  studentReciprocityInput: document.getElementById("student-reciprocity-input"),
  studentResonanceInput: document.getElementById("student-resonance-input"),
  studentDominanceInput: document.getElementById("student-dominance-input"),
  studentVoiceSelect: document.getElementById("student-voice-select"),
  studentVoiceInput: document.getElementById("student-voice-input"),
  studentRateInput: document.getElementById("student-rate-input"),
  studentPitchInput: document.getElementById("student-pitch-input"),
  studentVolumeInput: document.getElementById("student-volume-input"),
  loadLesson: document.getElementById("load-lesson"),
  saveCourseSetup: document.getElementById("save-course-setup"),
  exportCourseSetup: document.getElementById("export-course-setup"),
  importCourseSetup: document.getElementById("import-course-setup"),
  courseImportInput: document.getElementById("course-import-input"),
  saveStudentProfile: document.getElementById("save-student-profile"),
  generateStudentNote: document.getElementById("generate-student-note"),
  speakStudentNote: document.getElementById("speak-student-note"),
  stopStudentNote: document.getElementById("stop-student-note"),
  scoreResponse: document.getElementById("score-response"),
  stepOnce: document.getElementById("step-once"),
  toggleAuto: document.getElementById("toggle-auto"),
  reset: document.getElementById("reset"),
  previousActivity: document.getElementById("previous-activity"),
  nextActivity: document.getElementById("next-activity"),
  narrativeBack: document.getElementById("narrative-back"),
  narrativeNext: document.getElementById("narrative-next"),
  narrativeAuto: document.getElementById("narrative-auto"),
  applyLessonAuthoring: document.getElementById("apply-lesson-authoring"),
  resetLessonAuthoring: document.getElementById("reset-lesson-authoring"),
  exportAuthoredLesson: document.getElementById("export-authored-lesson"),
};

const canvas = document.getElementById("feed");
const ctx = canvas.getContext("2d");

const assetEls = {
  planetCore: document.getElementById("planet-core"),
  glyphUpper: document.getElementById("glyph-upper"),
  glyphLower: document.getElementById("glyph-lower"),
  glyphSymbols: document.getElementById("glyph-symbols"),
  streamMap: document.getElementById("stream-map"),
  nodeSheet: document.getElementById("node-sheet"),
  avatarSheet: document.getElementById("avatar-sheet"),
  signalSheet: document.getElementById("signal-sheet"),
};

let liveState = null;
let lessonLibrary = null;
let baseLessonLibrary = null;
let animationLibrary = null;
let activeLesson = null;
let courseState = null;
let currentStudentNote = null;
let autoTimer = null;
let activeActivityIndex = 0;
let activitySessions = new Map();
let activeUtterance = null;
let availableVoices = [];
let pageEnteredAt = performance.now();
let activityStartedAt = performance.now();
let puzzleSolveSamples = [];
let paceHistory = [];
let narrativeBeats = [];
let activeNarrativeIndex = 0;
let narrativeAutoMode = true;

function parseList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function directivePayload() {
  return {
    curiosity_bias: Number(controls.curiosity.value),
    equity_bias: Number(controls.equity.value),
    challenge_bias: Number(controls.challenge.value),
    reflection_bias: Number(controls.reflection.value),
  };
}

function currentPaceMetrics() {
  const now = performance.now();
  const averagePuzzleSeconds = puzzleSolveSamples.length
    ? puzzleSolveSamples.reduce((sum, value) => sum + value, 0) / puzzleSolveSamples.length
    : 0;
  const lastPuzzleSeconds = puzzleSolveSamples[puzzleSolveSamples.length - 1] || 0;
  return {
    page_minutes: (now - pageEnteredAt) / 60000,
    average_puzzle_seconds: averagePuzzleSeconds,
    last_puzzle_seconds: lastPuzzleSeconds,
    active_activity_seconds: (now - activityStartedAt) / 1000,
    solved_activity_count: puzzleSolveSamples.length,
  };
}

function recordSolvedActivity() {
  const elapsedSeconds = Math.max(1, (performance.now() - activityStartedAt) / 1000);
  puzzleSolveSamples = [...puzzleSolveSamples.slice(-11), elapsedSeconds];
  activityStartedAt = performance.now();
}

function resetPaceRuntime() {
  pageEnteredAt = performance.now();
  activityStartedAt = performance.now();
  puzzleSolveSamples = [];
  paceHistory = [];
}

function meter(value) {
  return Number(value ?? 0).toFixed(3);
}

function labelize(value) {
  return String(value || "")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function renderTags(target, items) {
  target.innerHTML = "";
  items.forEach((item) => {
    const node = document.createElement("span");
    node.className = "tag";
    node.textContent = item;
    target.appendChild(node);
  });
}

function renderStack(target, items, formatter) {
  target.innerHTML = "";
  items.forEach((item, index) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = formatter(item, index);
    target.appendChild(node);
  });
}

function renderLessonOptions() {
  controls.lessonSelect.innerHTML = "";
  lessonLibrary?.lessons?.forEach((lesson) => {
    const option = document.createElement("option");
    option.value = lesson.lesson_id;
    option.textContent = `${lesson.region}: ${lesson.title}`;
    controls.lessonSelect.appendChild(option);
  });
  if (activeLesson?.lesson_id) {
    controls.lessonSelect.value = activeLesson.lesson_id;
  }
}

function renderAuthoringStatus(message) {
  if (stateEls.authoringStatus) {
    stateEls.authoringStatus.textContent = message;
  }
}

function selectedAuthorAnimationIds() {
  return [...controls.authorAnimationPicker.querySelectorAll("input[type='checkbox']:checked")].map((input) => input.value);
}

function renderAuthorAnimationPicker(selectedIds = []) {
  if (!controls.authorAnimationPicker) {
    return;
  }
  controls.authorAnimationPicker.innerHTML = "";
  if (!animationLibrary?.animations?.length) {
    controls.authorAnimationPicker.innerHTML = '<div class="item">Animation library is still loading.</div>';
    return;
  }
  const selectedSet = new Set(selectedIds);
  animationLibrary.animations.forEach((animation) => {
    const label = document.createElement("label");
    label.className = "author-animation-option";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = animation.animation_id;
    checkbox.checked = selectedSet.has(animation.animation_id);
    const image = document.createElement("img");
    image.src = animation.asset_path;
    image.alt = animation.title;
    const meta = document.createElement("div");
    meta.innerHTML = `<strong>${escapeHtml(animation.title)}</strong><div>${escapeHtml(animation.description)}</div>`;
    label.appendChild(checkbox);
    label.appendChild(image);
    label.appendChild(meta);
    controls.authorAnimationPicker.appendChild(label);
  });
}

function tokensToText(tokens = []) {
  return tokens.map((token) => `${token.id || "token"} | ${token.label || "Label"} | ${token.hint || "Hint"}`).join("\n");
}

function parseAuthorTokens() {
  return controls.authorGameTokensInput.value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [rawId, rawLabel, ...hintParts] = line.split("|").map((part) => part.trim());
      const label = rawLabel || rawId || `Token ${index + 1}`;
      const tokenId = slugify(rawId || rawLabel || `token-${index + 1}`) || `token-${index + 1}`;
      return {
        id: tokenId,
        label,
        hint: hintParts.join(" | "),
      };
    });
}

function authoredCustomGame(lesson) {
  const requestedId = controls.authorGameActivityIdInput?.value?.trim();
  return (lesson?.activities || []).find((activity) => activity.type === "custom_game" && activity.activity_id === requestedId)
    || (lesson?.activities || []).find((activity) => activity.type === "custom_game")
    || null;
}

function buildAuthorStudioActivity() {
  const tokens = parseAuthorTokens();
  if (tokens.length < 2) {
    return null;
  }
  const completion = controls.authorGameCompletionInput.value.trim() || "The authored sequence is complete.";
  return {
    activity_id: controls.authorGameActivityIdInput.value.trim() || "author-studio-game",
    type: "custom_game",
    title: controls.authorGameTitleInput.value.trim() || "Author Studio Game",
    prompt: controls.authorGamePromptInput.value.trim() || "Arrange the authored sequence.",
    description: "Authored in the browser lesson studio.",
    difficulty: "steady",
    animation_ids: selectedAuthorAnimationIds(),
    success_message: completion,
    config: {
      game_type: "sequence_builder",
      support_text: controls.authorGameSupportInput.value.trim() || "Place the anchors in the strongest explanatory order.",
      completion_message: completion,
      tokens,
      correct_order: tokens.map((token) => token.id),
    },
  };
}

function renderAuthoringPreview(lesson) {
  if (!stateEls.authoringPreview) {
    return;
  }
  if (!lesson) {
    stateEls.authoringPreview.textContent = "";
    return;
  }
  const preview = {
    lesson_id: lesson.lesson_id,
    title: lesson.title,
    animation_ids: lesson.animation_ids || [],
    authored_custom_game: (lesson.activities || []).find((activity) => activity.type === "custom_game") || null,
  };
  stateEls.authoringPreview.textContent = JSON.stringify(preview, null, 2);
}

function populateAuthoringStudio(lesson) {
  if (!lesson) {
    renderAuthorAnimationPicker([]);
    renderAuthoringPreview(null);
    return;
  }
  const customGame = authoredCustomGame(lesson);
  controls.authorLessonTitleInput.value = lesson.title || "";
  controls.authorGameActivityIdInput.value = customGame?.activity_id || "author-studio-game";
  controls.authorGameTitleInput.value = customGame?.title || "Author Studio Game";
  controls.authorGamePromptInput.value = customGame?.prompt || "Arrange the authored sequence.";
  controls.authorGameSupportInput.value = customGame?.config?.support_text || "Place the anchors in the strongest explanatory order.";
  controls.authorGameCompletionInput.value = customGame?.config?.completion_message || customGame?.success_message || "The authored sequence is complete.";
  controls.authorGameTokensInput.value = tokensToText(customGame?.config?.tokens || []);
  renderAuthorAnimationPicker(lesson.animation_ids || customGame?.animation_ids || []);
  renderAuthoringPreview(lesson);
}

function applyLessonAuthoring() {
  if (!activeLesson) {
    renderAuthoringStatus("Load a lesson before applying authoring changes.");
    return;
  }
  const authoredLesson = deepClone(activeLesson);
  authoredLesson.title = controls.authorLessonTitleInput.value.trim() || authoredLesson.title;
  authoredLesson.animation_ids = selectedAuthorAnimationIds();
  const nextActivity = buildAuthorStudioActivity();
  const activityId = controls.authorGameActivityIdInput.value.trim() || "author-studio-game";
  authoredLesson.activities = (authoredLesson.activities || []).filter((activity) => activity.activity_id !== activityId);
  if (nextActivity) {
    authoredLesson.activities.push(nextActivity);
  }
  const lessonIndex = lessonLibrary?.lessons?.findIndex((lesson) => lesson.lesson_id === authoredLesson.lesson_id) ?? -1;
  if (lessonIndex >= 0) {
    lessonLibrary.lessons[lessonIndex] = authoredLesson;
  }
  activeLesson = authoredLesson;
  renderLessonOptions();
  resetLessonRuntime(activeLesson, 0);
  resetNarrativeWindow(activeLesson);
  renderLessonPanel({ lesson: activeLesson, lesson_mastery: [], mastery_overview: 0, lesson_depth: activeLesson.depth || { depth_score: 0 } });
  renderActivity();
  renderAuthoringPreview(activeLesson);
  renderAuthoringStatus(nextActivity
    ? `Applied authoring changes to ${activeLesson.title}. The lesson now includes ${activeLesson.animation_ids.length} animation pick(s) and the custom game ${nextActivity.title}.`
    : `Applied lesson animation changes to ${activeLesson.title}.`);
}

function restoreBaseLesson() {
  if (!activeLesson || !baseLessonLibrary?.lessons?.length) {
    renderAuthoringStatus("No base lesson is available to restore.");
    return;
  }
  const baseLesson = baseLessonLibrary.lessons.find((lesson) => lesson.lesson_id === activeLesson.lesson_id);
  if (!baseLesson) {
    renderAuthoringStatus("The packaged lesson could not be found for restoration.");
    return;
  }
  const restoredLesson = deepClone(baseLesson);
  const lessonIndex = lessonLibrary?.lessons?.findIndex((lesson) => lesson.lesson_id === restoredLesson.lesson_id) ?? -1;
  if (lessonIndex >= 0) {
    lessonLibrary.lessons[lessonIndex] = restoredLesson;
  }
  activeLesson = restoredLesson;
  renderLessonOptions();
  populateAuthoringStudio(activeLesson);
  resetLessonRuntime(activeLesson, 0);
  resetNarrativeWindow(activeLesson);
  renderLessonPanel({ lesson: activeLesson, lesson_mastery: [], mastery_overview: 0, lesson_depth: activeLesson.depth || { depth_score: 0 } });
  renderActivity();
  renderAuthoringStatus(`Restored the packaged lesson for ${activeLesson.title}.`);
}

function exportAuthoredLesson() {
  if (!activeLesson) {
    renderAuthoringStatus("No active lesson is available to export.");
    return;
  }
  const blob = new Blob([JSON.stringify(activeLesson, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(activeLesson.lesson_id || activeLesson.title || "authored-lesson") || "authored-lesson"}.json`;
  link.click();
  URL.revokeObjectURL(url);
  renderAuthoringStatus(`Exported ${activeLesson.title} as lesson JSON.`);
}

function lessonNarrativeBeats(lesson) {
  if (!lesson) {
    return [];
  }
  const beats = [];
  beats.push({
    title: `${labelize(lesson.subject || "lesson")} frame`,
    body: `${lesson.title || "This lesson"} asks how ${lesson.region || "the subject region"} should be understood through its central question.`,
    context: lesson.essential_question || "No essential question is set yet.",
  });
  (lesson.phases || []).forEach((phase, index) => {
    beats.push({
      title: `Phase ${index + 1}: ${phase.title}`,
      body: phase.purpose || "This phase advances the lesson arc.",
      context: phase.facilitator_move || phase.learner_signal || "No additional phase context provided.",
    });
  });
  (lesson.concept_threads || []).forEach((thread, index) => {
    beats.push({
      title: `Thread ${index + 1}: ${thread.label}`,
      body: thread.question || "This thread names a specialized subject focus.",
      context: thread.significance || "No thread significance provided.",
    });
  });
  if ((lesson.objectives || []).length) {
    beats.push({
      title: "Objective cluster",
      body: (lesson.objectives || []).slice(0, 3).join(" "),
      context: `Anchor terms: ${(lesson.vocabulary || []).slice(0, 4).join(", ") || "none yet"}.`,
    });
  }
  if ((lesson.discussion_prompts || []).length) {
    beats.push({
      title: "Seminar prompt",
      body: lesson.discussion_prompts[0],
      context: lesson.response_prompt || "Use the prompt to open the response studio.",
    });
  }
  return beats;
}

function renderNarrativeWindow() {
  if (!narrativeBeats.length) {
    stateEls.narrativeSubject.textContent = "Preparing lesson subject...";
    stateEls.narrativeProgress.textContent = "0 / 0";
    stateEls.narrativeStage.textContent = "A condensed subject narrative will appear once a lesson is active.";
    stateEls.narrativeBody.textContent = "";
    stateEls.narrativeContext.textContent = "";
    controls.narrativeBack.disabled = true;
    controls.narrativeNext.disabled = true;
    return;
  }
  const beat = narrativeBeats[activeNarrativeIndex] || narrativeBeats[0];
  stateEls.narrativeSubject.textContent = activeLesson?.title || "Lesson narrative";
  stateEls.narrativeProgress.textContent = `${activeNarrativeIndex + 1} / ${narrativeBeats.length}`;
  stateEls.narrativeStage.textContent = beat.title;
  stateEls.narrativeBody.textContent = beat.body;
  stateEls.narrativeContext.textContent = beat.context;
  controls.narrativeBack.disabled = activeNarrativeIndex <= 0;
  controls.narrativeNext.disabled = activeNarrativeIndex >= narrativeBeats.length - 1;
  controls.narrativeAuto.textContent = narrativeAutoMode ? "Auto Popups On" : "Auto Popups Off";
}

function resetNarrativeWindow(lesson) {
  narrativeBeats = lessonNarrativeBeats(lesson);
  activeNarrativeIndex = 0;
  renderNarrativeWindow();
}

function advanceNarrativeWindow() {
  if (!narrativeBeats.length) {
    return;
  }
  activeNarrativeIndex = Math.min(narrativeBeats.length - 1, activeNarrativeIndex + 1);
  renderNarrativeWindow();
}

function syncNarrativeToLessonState(state) {
  if (!narrativeAutoMode || !narrativeBeats.length) {
    return;
  }
  const activityFactor = Math.min(1, activeActivityIndex / Math.max((getActivities(activeLesson).length || 1) - 1, 1));
  const masteryFactor = Number(state?.mastery_overview ?? 0);
  const tickFactor = Math.min(1, Number(state?.tick ?? 0) / 12);
  const targetIndex = Math.min(
    narrativeBeats.length - 1,
    Math.round((0.34 * activityFactor + 0.36 * masteryFactor + 0.30 * tickFactor) * (narrativeBeats.length - 1)),
  );
  if (targetIndex !== activeNarrativeIndex) {
    activeNarrativeIndex = targetIndex;
    renderNarrativeWindow();
  }
}

function applyLessonDirective(lesson) {
  const directive = lesson?.recommended_directive;
  if (!directive) {
    return;
  }
  controls.curiosity.value = directive.curiosity_bias ?? controls.curiosity.value;
  controls.equity.value = directive.equity_bias ?? controls.equity.value;
  controls.challenge.value = directive.challenge_bias ?? controls.challenge.value;
  controls.reflection.value = directive.reflection_bias ?? controls.reflection.value;
}

function syncAvailableVoices() {
  if (!("speechSynthesis" in window)) {
    availableVoices = [];
    return;
  }
  availableVoices = [...window.speechSynthesis.getVoices()].sort((left, right) => left.name.localeCompare(right.name));
  renderVoiceOptions(activeStudentProfile()?.speech?.voice_name || controls.studentVoiceSelect.value || "");
}

function renderVoiceOptions(selectedName = "") {
  controls.studentVoiceSelect.innerHTML = "";
  const defaultOption = document.createElement("option");
  defaultOption.value = "";
  defaultOption.textContent = availableVoices.length ? "Browser default voice" : "Voice list unavailable";
  controls.studentVoiceSelect.appendChild(defaultOption);
  availableVoices.forEach((voice) => {
    const option = document.createElement("option");
    option.value = voice.name;
    option.textContent = `${voice.name} | ${voice.lang}`;
    controls.studentVoiceSelect.appendChild(option);
  });
  controls.studentVoiceSelect.value = selectedName || "";
}

function activeStudentProfile() {
  const activeStudentId = controls.studentSelect.value || courseState?.active_student_id;
  return courseState?.students?.find((student) => student.student_id === activeStudentId) ?? null;
}

function populateStudentForm(student) {
  controls.studentNameInput.value = student?.display_name || "";
  controls.studentArchetypeInput.value = student?.archetype || "steady learner";
  controls.studentSpiritualFrameInput.value = student?.spiritual_frame || "reflective";
  controls.studentStrengthsInput.value = (student?.strengths || []).join(", ");
  controls.studentSupportsInput.value = (student?.support_needs || []).join(", ");
  controls.studentInterestsInput.value = (student?.interests || []).join(", ");
  controls.studentModalitiesInput.value = (student?.preferred_modalities || []).join(", ");
  controls.studentNotesInput.value = student?.notes || "";
  controls.studentTrustInput.value = student?.egosphere?.trust ?? 0.5;
  controls.studentFearInput.value = student?.egosphere?.fear ?? 0.25;
  controls.studentAdaptabilityInput.value = student?.egosphere?.adaptability ?? 0.5;
  controls.studentReciprocityInput.value = student?.egosphere?.reciprocity ?? 0.5;
  controls.studentResonanceInput.value = student?.egosphere?.resonance ?? 0.5;
  controls.studentDominanceInput.value = student?.egosphere?.dominance ?? 0.0;
  renderVoiceOptions(student?.speech?.voice_name || "");
  controls.studentVoiceInput.value = student?.speech?.voice_hint || "";
  controls.studentRateInput.value = student?.speech?.rate ?? 1.0;
  controls.studentPitchInput.value = student?.speech?.pitch ?? 1.0;
  controls.studentVolumeInput.value = student?.speech?.volume ?? 1.0;
}

function buildStudentProfileFromForm() {
  const displayName = controls.studentNameInput.value.trim();
  const studentId = controls.studentSelect.value || slugify(displayName) || `student-${(courseState?.students?.length || 0) + 1}`;
  return {
    student_id: studentId,
    display_name: displayName,
    archetype: controls.studentArchetypeInput.value.trim() || "steady learner",
    spiritual_frame: controls.studentSpiritualFrameInput.value.trim() || "reflective",
    strengths: parseList(controls.studentStrengthsInput.value),
    support_needs: parseList(controls.studentSupportsInput.value),
    interests: parseList(controls.studentInterestsInput.value),
    preferred_modalities: parseList(controls.studentModalitiesInput.value),
    notes: controls.studentNotesInput.value.trim(),
    egosphere: {
      trust: Number(controls.studentTrustInput.value),
      fear: Number(controls.studentFearInput.value),
      adaptability: Number(controls.studentAdaptabilityInput.value),
      reciprocity: Number(controls.studentReciprocityInput.value),
      resonance: Number(controls.studentResonanceInput.value),
      dominance: Number(controls.studentDominanceInput.value),
    },
    speech: {
      voice_name: controls.studentVoiceSelect.value,
      voice_hint: controls.studentVoiceInput.value.trim(),
      rate: Number(controls.studentRateInput.value),
      pitch: Number(controls.studentPitchInput.value),
      volume: Number(controls.studentVolumeInput.value),
    },
  };
}

function buildCoursePayload(includeCurrentStudent = false) {
  const students = [...(courseState?.students || [])];
  if (includeCurrentStudent && controls.studentNameInput.value.trim()) {
    const currentStudent = buildStudentProfileFromForm();
    const existingIndex = students.findIndex((student) => student.student_id === currentStudent.student_id);
    if (existingIndex >= 0) {
      students[existingIndex] = currentStudent;
    } else {
      students.push(currentStudent);
    }
  }
  return {
    course_id: courseState?.course_id || "course-in-formation",
    title: controls.courseTitleInput.value.trim() || "Untitled Course",
    educator_name: controls.courseEducatorInput.value.trim(),
    course_notes: controls.courseNotesInput.value.trim(),
    active_student_id: controls.studentSelect.value || students[0]?.student_id || "",
    setup_complete: students.length > 0,
    god_profile: {
      conductor_name: controls.godNameInput.value.trim() || "GodAI Seminar Voice",
      tone: controls.godToneInput.value.trim() || "steady mercy",
      mercy_bias: Number(controls.godMercyInput.value),
      challenge_bias: Number(controls.godChallengeInput.value),
      wonder_bias: Number(controls.godWonderInput.value),
    },
    politeness_protocol: {
      greeting_template: controls.protocolGreetingInput.value.trim() || "Good to see you",
      affirmation_template: controls.protocolAffirmationInput.value.trim() || "Thank you for your thoughtful work",
      closing_template: controls.protocolClosingInput.value.trim() || "Take your time and proceed with care",
      redirection_template: controls.protocolRedirectionInput.value.trim() || "Let us return to one anchor at a time",
    },
    pace_profile: {
      reveal_controls: true,
      auto_pace_enabled: controls.paceAutoEnableInput.value !== "false",
      manual_pace_bias: Number(controls.paceManualInput.value),
      manual_clarity_bias: Number(controls.paceClarityInput.value),
      ai_authority: Number(controls.paceAiAuthorityInput.value),
      target_page_minutes: Number(controls.pacePageTargetInput.value),
      target_puzzle_seconds: Number(controls.pacePuzzleTargetInput.value),
      live_metrics: currentPaceMetrics(),
    },
    students,
  };
}

function renderStudentHistory(student, historyDigest = "") {
  if (!student) {
    stateEls.studentHistoryOutput.textContent = "No student history is available yet.";
    return;
  }
  const recentHistory = [...(student.lesson_history || [])]
    .sort((left, right) => (right.last_tick || 0) - (left.last_tick || 0))
    .slice(0, 2)
    .map((entry) => `${entry.lesson_title || entry.lesson_id}: mastery ${meter(entry.mastery_overview)} | response ${meter(entry.response_score)} | ${entry.compensation_mode}`)
    .join(" || ");
  stateEls.studentHistoryOutput.textContent = historyDigest || recentHistory || `${student.display_name || "This learner"} has no recorded lesson history yet.`;
}

function paceAssistProfile(flow) {
  if (!flow) {
    return {
      mode: "warming up",
      prompt: "The puzzle studio is waiting for live pace data before it starts adapting support.",
      hint: "Begin the lesson or step the simulation to activate live pacing.",
    };
  }
  if (flow.visual_obscurity_risk >= 0.56 || flow.solve_speed_drag >= 0.34 || flow.page_duration_drag >= 0.32) {
    return {
      mode: "scaffolded",
      prompt: "Puzzle support is widening. The studio will lean on calmer prompts, clearer recaps, and single-anchor guidance.",
      hint: flow.learner_prompt,
    };
  }
  if (flow.final_pace_rate >= 0.7 && flow.solve_speed_drag <= 0.12 && flow.page_duration_drag <= 0.1) {
    return {
      mode: "accelerated",
      prompt: "Puzzle support is tightening. The studio expects faster recognition and lighter scaffolding.",
      hint: "Advance with shorter checks and stronger inference.",
    };
  }
  return {
    mode: "standard",
    prompt: "Puzzle support is balanced. The studio keeps guidance present without slowing the arc.",
    hint: "Use the main evidence line, then widen only when the anchor is secure.",
  };
}

function renderPaceSparkline() {
  if (!paceHistory.length) {
    stateEls.livePaceSparklineFill.setAttribute("d", "");
    stateEls.livePaceSparklinePath.setAttribute("d", "");
    return;
  }
  const width = 180;
  const height = 46;
  const points = paceHistory.slice(-18);
  const coordinates = points.map((point, index) => {
    const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
    const y = height - (height - 6) * Math.max(0, Math.min(1, point));
    return [x, y];
  });
  const linePath = coordinates.map(([x, y], index) => `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`).join(" ");
  const fillPath = `${linePath} L ${width} ${height} L 0 ${height} Z`;
  stateEls.livePaceSparklinePath.setAttribute("d", linePath);
  stateEls.livePaceSparklineFill.setAttribute("d", fillPath);
}

function updatePaceHistory(flow) {
  if (!flow) {
    return;
  }
  paceHistory = [...paceHistory.slice(-17), Number(flow.final_pace_rate ?? 0.5)];
  renderPaceSparkline();
}

function paceBranchProfile(flow, activity) {
  const assist = paceAssistProfile(flow);
  if (!activity) {
    return {
      note: "No active puzzle branch yet.",
      revealExplanationEarly: false,
      highlightSupportCards: false,
      accelerateCopy: false,
      mode: assist.mode,
    };
  }
  if (assist.mode === "scaffolded") {
    return {
      note: `Scaffolded branch: ${activity.title || "this activity"} will foreground one anchor at a time and keep explanatory support visible.`,
      revealExplanationEarly: true,
      highlightSupportCards: true,
      accelerateCopy: false,
      mode: assist.mode,
    };
  }
  if (assist.mode === "accelerated") {
    return {
      note: `Accelerated branch: ${activity.title || "this activity"} trims advance hints so the learner can move on inference and recognition.`,
      revealExplanationEarly: false,
      highlightSupportCards: false,
      accelerateCopy: true,
      mode: assist.mode,
    };
  }
  return {
    note: `Standard branch: ${activity.title || "this activity"} keeps normal support and explanation timing.`,
    revealExplanationEarly: false,
    highlightSupportCards: false,
    accelerateCopy: false,
    mode: assist.mode,
  };
}

function renderLivePaceMeter(flow) {
  if (!flow) {
    stateEls.livePaceMeter.textContent = "AI pace meter awaiting live data.";
    stateEls.livePaceMeterSub.textContent = "The AI will surface pace, step count, and interval once lesson flow is active.";
    stateEls.puzzleAssistOutput.textContent = "Puzzle pacing assist will appear once the lesson flow settles.";
    stateEls.puzzleBranchOutput.textContent = "Puzzle branching will reflect the current pace mode once lesson flow is active.";
    renderPaceSparkline();
    return;
  }
  const assist = paceAssistProfile(flow);
  stateEls.livePaceMeter.textContent = `${labelize(flow.final_pace_label)} pace | ${flow.recommended_step_count} steps | ${flow.auto_run_interval_ms} ms`;
  stateEls.livePaceMeterSub.textContent = `Risk ${meter(flow.visual_obscurity_risk)} | page drag ${meter(flow.page_duration_drag)} | solve drag ${meter(flow.solve_speed_drag)} | support ${assist.mode}.`;
  stateEls.puzzleAssistOutput.textContent = `${labelize(assist.mode)} support. ${assist.prompt} ${assist.hint}`;
  updatePaceHistory(flow);
}

function renderLessonFlow(flow) {
  if (!flow) {
    stateEls.paceTheoryOutput.textContent = "Lesson pace theory has not been evaluated yet.";
    stateEls.paceCompensationOutput.textContent = "No pace compensation is active.";
    stateEls.paceVisualOutput.textContent = "Visual clarity guidance is unavailable.";
    stateEls.paceRuntimeOutput.textContent = "Runtime pace metrics are unavailable.";
    stateEls.feedFocusNote.textContent = "";
    renderLivePaceMeter(null);
    return;
  }
  stateEls.paceTheoryOutput.textContent = `Theory ${labelize(flow.theory_signal)} | pace ${meter(flow.pace_pressure)} | erraticism ${meter(flow.erraticism)} | lesson drag ${meter(flow.long_term_drag)}.`;
  stateEls.paceCompensationOutput.textContent = `Compensation ${labelize(flow.compensation_mode)} | strength ${meter(flow.compensation_strength)} | final pace ${labelize(flow.final_pace_label)} (${meter(flow.final_pace_rate)}). ${flow.educator_prompt}`;
  stateEls.paceVisualOutput.textContent = `Visual clarity ${meter(flow.display_clarity)} | obscurity risk ${meter(flow.visual_obscurity_risk)}. ${flow.learner_prompt}`;
  stateEls.paceRuntimeOutput.textContent = `AI pace from page drag ${meter(flow.page_duration_drag)} and solve drag ${meter(flow.solve_speed_drag)}. Suggested steps ${flow.recommended_step_count} | auto interval ${flow.auto_run_interval_ms} ms.`;
  stateEls.feedFocusNote.textContent = `${labelize(flow.compensation_mode)}: ${flow.learner_prompt}`;
  assetEls.streamMap.style.opacity = String(flow.feed_opacity ?? 0.8);
  assetEls.nodeSheet.style.opacity = String(Math.max(0.08, (flow.feed_opacity ?? 0.8) - 0.22));
  renderLivePaceMeter(flow);
  if (controls.paceAutoEnableInput.value !== "false") {
    controls.steps.value = String(flow.recommended_step_count || controls.steps.value);
  }
}

function renderCoursePanel(course) {
  courseState = course || { students: [], god_profile: {} };
  controls.courseTitleInput.value = courseState.title || "";
  controls.courseEducatorInput.value = courseState.educator_name || "";
  controls.courseNotesInput.value = courseState.course_notes || "";
  controls.godNameInput.value = courseState.god_profile?.conductor_name || "GodAI Seminar Voice";
  controls.godToneInput.value = courseState.god_profile?.tone || "steady mercy";
  controls.godMercyInput.value = courseState.god_profile?.mercy_bias ?? 0.78;
  controls.godChallengeInput.value = courseState.god_profile?.challenge_bias ?? 0.62;
  controls.godWonderInput.value = courseState.god_profile?.wonder_bias ?? 0.81;
  controls.protocolGreetingInput.value = courseState.politeness_protocol?.greeting_template || "Good to see you";
  controls.protocolAffirmationInput.value = courseState.politeness_protocol?.affirmation_template || "Thank you for your thoughtful work";
  controls.protocolClosingInput.value = courseState.politeness_protocol?.closing_template || "Take your time and proceed with care";
  controls.protocolRedirectionInput.value = courseState.politeness_protocol?.redirection_template || "Let us return to one anchor at a time";
  controls.paceAutoEnableInput.value = courseState.pace_profile?.auto_pace_enabled === false ? "false" : "true";
  controls.paceManualInput.value = courseState.pace_profile?.manual_pace_bias ?? 0.5;
  controls.paceClarityInput.value = courseState.pace_profile?.manual_clarity_bias ?? 0.72;
  controls.paceAiAuthorityInput.value = courseState.pace_profile?.ai_authority ?? 0.62;
  controls.pacePageTargetInput.value = courseState.pace_profile?.target_page_minutes ?? 6;
  controls.pacePuzzleTargetInput.value = courseState.pace_profile?.target_puzzle_seconds ?? 90;

  controls.studentSelect.innerHTML = "";
  (courseState.students || []).forEach((student) => {
    const option = document.createElement("option");
    option.value = student.student_id;
    option.textContent = `${student.display_name || student.student_id} | ${student.archetype || "student"}`;
    controls.studentSelect.appendChild(option);
  });
  if ((courseState.students || []).length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No student profiles yet";
    controls.studentSelect.appendChild(option);
  }

  const activeStudentId = courseState.active_student_id || courseState.students?.[0]?.student_id || "";
  controls.studentSelect.value = activeStudentId;
  populateStudentForm(activeStudentProfile());
  renderStudentHistory(activeStudentProfile());
  stateEls.courseStatus.textContent = courseState.setup_complete
    ? `Course setup saved for ${courseState.title || "this course"} with ${courseState.students.length} student profile(s).`
    : "Course setup has not been saved yet.";
}

function renderStudentNote(note) {
  currentStudentNote = note;
  stateEls.studentNoteOutput.textContent = note?.specialized_note || "No personalized student note has been generated yet.";
  stateEls.educatorNoteOutput.textContent = note?.educator_note || "";
  stateEls.godGuidanceOutput.textContent = note
    ? `${note.guidance.conductor_name} | omen ${note.guidance.omen} | style ${note.guidance.recommended_style} | mercy ${note.guidance.mercy_window ? "open" : "closed"} | pressure ${meter(note.guidance.pressure_scale)}`
    : "";
  renderStudentHistory(activeStudentProfile(), note?.history_digest || "");
  renderLessonFlow(note?.lesson_flow || liveState?.lesson_flow || null);
}

function stopSpeechPlayback() {
  if (!("speechSynthesis" in window)) {
    return;
  }
  window.speechSynthesis.cancel();
  activeUtterance = null;
}

function speakStudentNote() {
  if (!("speechSynthesis" in window) || !currentStudentNote?.speech_text) {
    stateEls.godGuidanceOutput.textContent = "Speech synthesis is unavailable in this browser or no note has been generated yet.";
    return;
  }
  stopSpeechPlayback();
  const utterance = new SpeechSynthesisUtterance(currentStudentNote.speech_text);
  utterance.rate = Number(currentStudentNote.speech?.rate ?? 1.0);
  utterance.pitch = Number(currentStudentNote.speech?.pitch ?? 1.0);
  utterance.volume = Number(currentStudentNote.speech?.volume ?? 1.0);
  const voiceName = String(currentStudentNote.speech?.voice_name || "");
  const voiceHint = String(currentStudentNote.speech?.voice_hint || "").toLowerCase();
  const voices = window.speechSynthesis.getVoices();
  const matchingVoice = voices.find((voice) => voice.name === voiceName)
    || voices.find((voice) => voice.name.toLowerCase().includes(voiceHint) || voice.lang.toLowerCase().includes(voiceHint));
  if (matchingVoice) {
    utterance.voice = matchingVoice;
  }
  activeUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

function findLessonById(lessonId) {
  return lessonLibrary?.lessons?.find((lesson) => lesson.lesson_id === lessonId) ?? null;
}

function getActivities(lesson) {
  if (lesson?.activities?.length) {
    return lesson.activities;
  }
  if (lesson?.puzzle?.type) {
    return [{ ...lesson.puzzle, activity_id: lesson.puzzle.activity_id || lesson.puzzle.type }];
  }
  return [];
}

function animationsForIds(animationIds = []) {
  if (!animationLibrary?.animations?.length) {
    return [];
  }
  return animationIds
    .map((animationId) => animationLibrary.animations.find((item) => item.animation_id === animationId))
    .filter(Boolean);
}

function animationIdsForActivity(activity) {
  const lessonAnimationIds = activeLesson?.animation_ids || [];
  const activityAnimationIds = activity?.animation_ids || [];
  return [...new Set([...activityAnimationIds, ...lessonAnimationIds])];
}

function renderAnimationGallery(lesson, activity = null) {
  if (!stateEls.lessonAnimations) {
    return;
  }
  const selectedAnimations = animationsForIds(activity ? animationIdsForActivity(activity) : lesson?.animation_ids || []);
  stateEls.lessonAnimations.innerHTML = "";
  if (!selectedAnimations.length) {
    stateEls.lessonAnimations.innerHTML = '<div class="item">No lesson animation picks are assigned yet.</div>';
    return;
  }

  selectedAnimations.forEach((animation) => {
    const card = document.createElement("article");
    card.className = "animation-card";
    const swatches = (animation.palette || [])
      .map((color) => `<span style="background:${escapeHtml(color)}"></span>`)
      .join("");
    card.innerHTML = `
      <img src="${escapeHtml(animation.asset_path)}" alt="${escapeHtml(animation.title)}">
      <div>
        <strong>${escapeHtml(animation.title)}</strong>
        <div>${escapeHtml(animation.description)}</div>
        <p>${escapeHtml(labelize(animation.motion))} | ${escapeHtml(labelize(animation.theme))}</p>
        <div class="animation-swatches">${swatches}</div>
      </div>
    `;
    stateEls.lessonAnimations.appendChild(card);
  });
}

function currentActivity() {
  const activities = getActivities(activeLesson);
  return activities[activeActivityIndex] ?? null;
}

function activitySessionKey(lesson, activity) {
  return `${lesson?.lesson_id || "lesson"}:${activity?.activity_id || activity?.type || "activity"}`;
}

function updatePuzzleFeedback(message, mode = "neutral") {
  stateEls.puzzleFeedback.textContent = message;
  stateEls.puzzleFeedback.dataset.mode = mode;
}

function createActivitySession(activity) {
  if (!activity) {
    return null;
  }
  if (activity.type === "timeline_order") {
    return {
      type: "timeline_order",
      orderedItems: [...(activity.items || [])],
      items: [...(activity.items || [])].sort((left, right) => left.label.localeCompare(right.label)),
      expectedIndex: 0,
      solved: false,
    };
  }
  if (activity.type === "match_pairs") {
    const pairs = activity.pairs || [];
    return {
      type: "match_pairs",
      leftItems: pairs.map((pair, index) => ({ id: `left-${index}`, text: pair.left, match: pair.right })),
      rightItems: [...pairs.map((pair, index) => ({ id: `right-${index}`, text: pair.right, match: pair.left }))].reverse(),
      selectedLeft: null,
      matches: [],
      solved: false,
    };
  }
  if (activity.type === "multiple_choice") {
    return {
      type: "multiple_choice",
      selectedIndex: null,
      solved: false,
    };
  }
  if (activity.type === "evidence_select") {
    return {
      type: "evidence_select",
      selectedIds: [],
      reviewed: false,
      solved: false,
    };
  }
  if (activity.type === "custom_game") {
    return {
      type: "custom_game",
      gameType: activity.config?.game_type || "sequence_builder",
      selectedIds: [],
      attempts: 0,
      solved: false,
    };
  }
  return { type: activity.type || "unknown", solved: false };
}

function ensureActivitySession() {
  const activity = currentActivity();
  if (!activeLesson || !activity) {
    return null;
  }
  const key = activitySessionKey(activeLesson, activity);
  if (!activitySessions.has(key)) {
    activitySessions.set(key, createActivitySession(activity));
  }
  return activitySessions.get(key);
}

function resetLessonRuntime(lesson, nextIndex = 0) {
  activeLesson = lesson;
  activitySessions = new Map();
  activeActivityIndex = nextIndex;
  activityStartedAt = performance.now();
  ensureActivitySession();
}

function syncActiveLessonFromState(state) {
  if (!state?.lesson?.title) {
    return;
  }
  activeLesson = findLessonById(state.lesson.lesson_id) || state.lesson;
  controls.lessonSelect.value = activeLesson.lesson_id || controls.lessonSelect.value;
  populateAuthoringStudio(activeLesson);
}

function renderActivityRail() {
  stateEls.activityRail.innerHTML = "";
  const activities = getActivities(activeLesson);
  activities.forEach((activity, index) => {
    const pill = document.createElement("button");
    pill.type = "button";
    pill.className = "activity-pill";
    pill.textContent = `${index + 1}. ${activity.title || activity.type}`;
    const session = activitySessions.get(activitySessionKey(activeLesson, activity));
    pill.dataset.state = index === activeActivityIndex ? "active" : session?.solved ? "complete" : "open";
    pill.addEventListener("click", () => {
      activeActivityIndex = index;
      activityStartedAt = performance.now();
      ensureActivitySession();
      renderActivityRail();
      renderActivity();
    });
    stateEls.activityRail.appendChild(pill);
  });
  controls.previousActivity.disabled = activeActivityIndex <= 0;
  controls.nextActivity.disabled = activeActivityIndex >= Math.max(activities.length - 1, 0);
}

function renderActivity() {
  stateEls.puzzleBoard.innerHTML = "";
  const activity = currentActivity();
  const session = ensureActivitySession();
  const assist = paceAssistProfile(liveState?.lesson_flow || currentStudentNote?.lesson_flow || null);
  const branch = paceBranchProfile(liveState?.lesson_flow || currentStudentNote?.lesson_flow || null, activity);
  renderActivityRail();
  renderNarrativeWindow();
  renderAnimationGallery(activeLesson, activity);

  if (!activity || !session) {
    stateEls.puzzleTitle.textContent = "No activity loaded";
    stateEls.puzzlePrompt.textContent = "";
    stateEls.puzzleBranchOutput.textContent = "Puzzle branching will reflect the current pace mode once lesson flow is active.";
    updatePuzzleFeedback("Choose a lesson to begin the learning studio.");
    renderAnimationGallery(activeLesson, null);
    return;
  }

  stateEls.puzzleBranchOutput.textContent = `${labelize(branch.mode)} branch. ${branch.note}`;
  stateEls.puzzleTitle.textContent = activity.title || "Lesson Activity";
  stateEls.puzzlePrompt.textContent = `${activity.prompt || activity.description || ""} ${assist.mode === "scaffolded" ? assist.hint : ""}`.trim();

  if (session.type === "timeline_order") {
    if (branch.revealExplanationEarly && activity.description) {
      const note = document.createElement("div");
      note.className = "item branch-note";
      note.dataset.mode = branch.mode;
      note.textContent = activity.description;
      stateEls.puzzleBoard.appendChild(note);
    }
    updatePuzzleFeedback(session.solved ? (activity.success_message || "Activity complete.") : assist.mode === "scaffolded" ? "Select the earliest phase first, then pause and restate the anchor." : "Select the earliest phase first.", session.solved ? "success" : "neutral");
    session.items.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "puzzle-chip timeline-chip";
      button.textContent = item.label;
      const orderedIndex = session.orderedItems.findIndex((orderedItem) => orderedItem.id === item.id);
      const isLocked = orderedIndex < session.expectedIndex;
      button.dataset.state = isLocked ? "locked" : "open";
      button.disabled = isLocked || session.solved;
      button.addEventListener("click", () => {
        const expectedItem = session.orderedItems[session.expectedIndex];
        if (expectedItem?.id === item.id) {
          session.expectedIndex += 1;
          if (session.expectedIndex >= session.orderedItems.length) {
            session.solved = true;
            recordSolvedActivity();
            updatePuzzleFeedback(activity.success_message || "Activity complete.", "success");
          } else {
            updatePuzzleFeedback(`Placed ${item.label} in sequence.`, "success");
          }
          renderActivity();
          return;
        }
        updatePuzzleFeedback(assist.mode === "scaffolded" ? `Try an earlier phase before ${item.label}, then follow the main anchor again.` : `Try an earlier phase before ${item.label}.`, "caution");
      });
      stateEls.puzzleBoard.appendChild(button);
    });
    return;
  }

  if (session.type === "match_pairs") {
    if (branch.revealExplanationEarly && activity.description) {
      const note = document.createElement("div");
      note.className = "item branch-note";
      note.dataset.mode = branch.mode;
      note.textContent = activity.description;
      stateEls.puzzleBoard.appendChild(note);
    }
    updatePuzzleFeedback(session.solved ? (activity.success_message || "Activity complete.") : assist.mode === "accelerated" ? "Choose and match quickly; the core structure should already be visible." : "Choose a civic element, then match its function.", session.solved ? "success" : "neutral");
    const leftColumn = document.createElement("div");
    leftColumn.className = "puzzle-column";
    const rightColumn = document.createElement("div");
    rightColumn.className = "puzzle-column";

    session.leftItems.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "puzzle-chip";
      button.textContent = item.text;
      const isMatched = session.matches.some((match) => match.left === item.text);
      button.disabled = isMatched || session.solved;
      button.dataset.state = session.selectedLeft?.text === item.text ? "selected" : isMatched ? "locked" : "open";
      button.addEventListener("click", () => {
        session.selectedLeft = item;
        updatePuzzleFeedback(`Now choose the matching function for ${item.text}.`);
        renderActivity();
      });
      leftColumn.appendChild(button);
    });

    session.rightItems.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "puzzle-chip";
      button.textContent = item.text;
      const isMatched = session.matches.some((match) => match.right === item.text);
      button.disabled = isMatched || session.solved;
      button.dataset.state = isMatched ? "locked" : "open";
      button.addEventListener("click", () => {
        if (!session.selectedLeft || session.solved) {
          updatePuzzleFeedback("Choose an item from the left column first.", "caution");
          return;
        }
        if (session.selectedLeft.match === item.text) {
          session.matches.push({ left: session.selectedLeft.text, right: item.text });
          session.selectedLeft = null;
          if (session.matches.length === session.leftItems.length) {
            session.solved = true;
            recordSolvedActivity();
            updatePuzzleFeedback(activity.success_message || "Activity complete.", "success");
          } else {
            updatePuzzleFeedback("Matched correctly. Continue the network.", "success");
          }
          renderActivity();
          return;
        }
          updatePuzzleFeedback(assist.mode === "scaffolded" ? "That function belongs elsewhere. Return to one civic anchor and compare again slowly." : "That function belongs elsewhere. Try again with a quieter comparison.", "caution");
      });
      rightColumn.appendChild(button);
    });

    stateEls.puzzleBoard.appendChild(leftColumn);
    stateEls.puzzleBoard.appendChild(rightColumn);
    return;
  }

  if (session.type === "multiple_choice") {
    if (branch.revealExplanationEarly && activity.explanation) {
      const note = document.createElement("div");
      note.className = "item branch-note";
      note.dataset.mode = branch.mode;
      note.textContent = activity.explanation;
      stateEls.puzzleBoard.appendChild(note);
    }
    updatePuzzleFeedback(session.solved ? (activity.success_message || activity.explanation || "Activity complete.") : assist.mode === "scaffolded" ? "Choose the option that best fits the lesson logic, then explain to yourself why the others fall away." : "Choose the option that best fits the lesson logic.", session.solved ? "success" : "neutral");
    activity.choices.forEach((choice, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "puzzle-chip";
      button.textContent = choice;
      const isSelected = session.selectedIndex === index;
      button.dataset.state = isSelected ? "selected" : "open";
      button.disabled = session.solved && index !== Number(activity.answer_index);
      button.addEventListener("click", () => {
        session.selectedIndex = index;
        if (index === Number(activity.answer_index)) {
          session.solved = true;
          recordSolvedActivity();
          updatePuzzleFeedback(activity.success_message || activity.explanation || "Correct.", "success");
        } else {
          updatePuzzleFeedback(branch.accelerateCopy ? "Not quite. Re-read the option set and trust the stronger structural cue." : activity.explanation || "Try the option that best explains the structure of power.", "caution");
        }
        renderActivity();
      });
      stateEls.puzzleBoard.appendChild(button);
    });
    return;
  }

  if (session.type === "evidence_select") {
    const supportIds = (activity.items || [])
      .filter((item) => item.role === "support")
      .map((item) => item.id);
    const selectedSet = new Set(session.selectedIds);
    const supportedSelectedCount = supportIds.filter((id) => selectedSet.has(id)).length;

    updatePuzzleFeedback(
      session.solved
        ? (activity.success_message || activity.explanation || "Activity complete.")
        : session.reviewed
          ? `You identified ${supportedSelectedCount} of ${supportIds.length} core evidence cards. Refine the set and review again.`
          : assist.mode === "scaffolded"
            ? "Select the cards that directly support the lesson claim, then review the set one anchor at a time."
            : "Select the cards that directly support the lesson claim, then review the set.",
      session.solved ? "success" : session.reviewed ? "caution" : "neutral",
    );

    (activity.items || []).forEach((item, index) => {
      const itemId = item.id || `evidence-${index}`;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "puzzle-chip evidence-chip";
      button.textContent = item.label || item.text || `Evidence ${index + 1}`;
      const isSelected = selectedSet.has(itemId);
      const isSupport = item.role === "support";

      if (session.reviewed || session.solved) {
        if (isSupport) {
          button.dataset.state = "correct";
        } else if (isSelected) {
          button.dataset.state = "caution";
        } else {
          button.dataset.state = isSelected ? "selected" : "open";
        }
      } else if (branch.highlightSupportCards && isSupport) {
        button.dataset.state = "correct";
      } else {
        button.dataset.state = isSelected ? "selected" : "open";
      }

      button.disabled = session.solved;
      button.addEventListener("click", () => {
        if (session.solved) {
          return;
        }
        if (selectedSet.has(itemId)) {
          session.selectedIds = session.selectedIds.filter((value) => value !== itemId);
        } else {
          session.selectedIds = [...session.selectedIds, itemId];
        }
        session.reviewed = false;
        renderActivity();
      });
      stateEls.puzzleBoard.appendChild(button);
    });

    const reviewButton = document.createElement("button");
    reviewButton.type = "button";
    reviewButton.className = "puzzle-chip evidence-review";
    reviewButton.textContent = session.solved ? "Evidence set complete" : "Review evidence set";
    reviewButton.disabled = session.solved || session.selectedIds.length === 0;
    reviewButton.addEventListener("click", () => {
      const selectedIds = [...session.selectedIds].sort();
      const sortedSupportIds = [...supportIds].sort();
      session.reviewed = true;
      session.solved = selectedIds.length === sortedSupportIds.length && selectedIds.every((value, index) => value === sortedSupportIds[index]);
      if (session.solved) {
        recordSolvedActivity();
        updatePuzzleFeedback(activity.success_message || activity.explanation || "Evidence aligned.", "success");
      } else {
        updatePuzzleFeedback(activity.explanation || "Recheck which cards directly support the lesson claim.", "caution");
      }
      renderActivity();
    });
    stateEls.puzzleBoard.appendChild(reviewButton);

    if (activity.explanation && (!branch.accelerateCopy || session.reviewed || session.solved || branch.revealExplanationEarly)) {
      const note = document.createElement("div");
      note.className = "item evidence-note";
      note.textContent = activity.explanation;
      stateEls.puzzleBoard.appendChild(note);
    }
    return;
  }

  if (session.type === "custom_game") {
    const gameConfig = activity.config || {};
    const tokens = gameConfig.tokens || [];
    const correctOrder = gameConfig.correct_order || [];
    const selectedSet = new Set(session.selectedIds);

    updatePuzzleFeedback(
      session.solved
        ? (gameConfig.completion_message || activity.success_message || "Custom game complete.")
        : gameConfig.support_text || "Build the authored sequence one anchor at a time.",
      session.solved ? "success" : "neutral",
    );

    const board = document.createElement("div");
    board.className = "custom-game-board";

    const currentSequence = document.createElement("div");
    currentSequence.className = "custom-game-sequence";
    if (session.selectedIds.length) {
      session.selectedIds.forEach((tokenId, index) => {
        const token = tokens.find((item) => item.id === tokenId);
        const chip = document.createElement("div");
        chip.className = "custom-sequence-chip";
        chip.textContent = `${index + 1}. ${token?.label || tokenId}`;
        currentSequence.appendChild(chip);
      });
    } else {
      const chip = document.createElement("div");
      chip.className = "custom-sequence-chip";
      chip.textContent = "No sequence placed yet.";
      currentSequence.appendChild(chip);
    }
    board.appendChild(currentSequence);

    const tokenGrid = document.createElement("div");
    tokenGrid.className = "custom-hint-grid";
    tokens.forEach((token) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "custom-hint-card";
      button.disabled = session.solved || selectedSet.has(token.id);
      button.innerHTML = `<strong>${escapeHtml(token.label)}</strong><div>${escapeHtml(token.hint || "")}</div>`;
      button.addEventListener("click", () => {
        if (session.solved) {
          return;
        }
        const nextSelection = [...session.selectedIds, token.id];
        const expectedPrefix = correctOrder.slice(0, nextSelection.length);
        const isCorrectPrefix = nextSelection.every((value, index) => value === expectedPrefix[index]);
        if (!isCorrectPrefix) {
          session.attempts += 1;
          updatePuzzleFeedback(
            assist.mode === "scaffolded"
              ? `That order blurs the main line. ${gameConfig.support_text || "Return to the first anchor and rebuild slowly."}`
              : "That placement breaks the authored sequence. Try a different starting anchor.",
            "caution",
          );
          if (assist.mode === "scaffolded") {
            session.selectedIds = [];
          }
          renderActivity();
          return;
        }
        session.selectedIds = nextSelection;
        if (session.selectedIds.length === correctOrder.length) {
          session.solved = true;
          recordSolvedActivity();
          updatePuzzleFeedback(gameConfig.completion_message || activity.success_message || "Custom game complete.", "success");
        }
        renderActivity();
      });
      tokenGrid.appendChild(button);
    });
    board.appendChild(tokenGrid);

    const actions = document.createElement("div");
    actions.className = "button-row custom-game-actions";
    const resetButton = document.createElement("button");
    resetButton.type = "button";
    resetButton.textContent = "Reset sequence";
    resetButton.disabled = session.solved && session.selectedIds.length === 0;
    resetButton.addEventListener("click", () => {
      session.selectedIds = [];
      session.solved = false;
      renderActivity();
    });
    actions.appendChild(resetButton);
    board.appendChild(actions);

    stateEls.puzzleBoard.appendChild(board);
    return;
  }

  updatePuzzleFeedback("This activity type is scaffolded but not yet rendered.", "caution");
}

function renderLessonPanel(state) {
  const lesson = state.lesson?.title ? state.lesson : activeLesson;
  if (!lesson) {
    stateEls.lessonTitle.textContent = "No lesson loaded";
    stateEls.lessonMeta.textContent = "";
    stateEls.lessonQuestion.textContent = "";
    stateEls.lessonObjectives.innerHTML = "";
    stateEls.lessonNotes.innerHTML = "";
    stateEls.lessonPhases.innerHTML = "";
    stateEls.lessonThreads.innerHTML = "";
    stateEls.lessonPrompts.innerHTML = "";
    stateEls.lessonRubric.innerHTML = "";
    renderTags(stateEls.lessonVocabulary, []);
    renderTags(stateEls.lessonFigures, []);
    renderTags(stateEls.lessonEras, []);
    stateEls.lessonSource.textContent = "";
    stateEls.lessonSourceAttribution.textContent = "";
    stateEls.masteryOverview.textContent = "0.000";
    stateEls.lessonDepth.textContent = "0.000";
    stateEls.responsePrompt.textContent = "";
    return;
  }

  stateEls.lessonTitle.textContent = lesson.title;
  stateEls.lessonMeta.textContent = [lesson.subject, lesson.region, lesson.era].filter(Boolean).join("  |  ");
  stateEls.lessonQuestion.textContent = lesson.essential_question || "A lesson question has not been supplied.";
  stateEls.masteryOverview.textContent = meter(state.mastery_overview ?? 0);
  stateEls.lessonDepth.textContent = meter(state.lesson_depth?.depth_score ?? lesson.depth?.depth_score ?? 0);

  stateEls.lessonObjectives.innerHTML = "";
  const masteryRows = state.lesson_mastery || [];
  lesson.objectives.forEach((objective, index) => {
    const row = masteryRows[index];
    const node = document.createElement("div");
    node.className = "item objective-item";
    node.innerHTML = `
      <strong>${objective}</strong>
      <div>mastery ${meter(row?.score ?? 0)} | emphasis ${row?.focus ?? "balanced growth"}</div>
    `;
    stateEls.lessonObjectives.appendChild(node);
  });

  renderStack(stateEls.lessonNotes, lesson.teaching_notes || [], (note, index) => `<strong>Note ${index + 1}</strong><div>${note}</div>`);
  renderStack(stateEls.lessonPhases, lesson.phases || [], (phase, index) => `<strong>Phase ${index + 1}: ${phase.title}</strong><div>${phase.purpose}</div><div>${phase.facilitator_move}</div>`);
  renderTags(stateEls.lessonVocabulary, lesson.vocabulary || []);
  renderTags(stateEls.lessonFigures, lesson.key_figures || []);
  renderAnimationGallery(lesson, currentActivity());
  renderStack(stateEls.lessonThreads, lesson.concept_threads || [], (thread) => `<strong>${thread.label}</strong><div>${thread.question}</div><div>${thread.significance}</div>`);
  renderStack(stateEls.lessonPrompts, lesson.discussion_prompts || [], (prompt, index) => `<strong>Prompt ${index + 1}</strong><div>${prompt}</div>`);
  renderStack(stateEls.lessonRubric, lesson.response_rubric || [], (dimension) => `<strong>${dimension.label}</strong><div>weight ${meter(dimension.weight)}</div><div>${dimension.guidance}</div>`);
  renderTags(stateEls.lessonEras, lesson.eras || []);
  stateEls.lessonSource.textContent = lesson.source_excerpt || "No source excerpt is loaded.";
  stateEls.lessonSourceAttribution.textContent = lesson.source_attribution || "";
  stateEls.responsePrompt.textContent = lesson.response_prompt || "Respond to the lesson with a short analytical paragraph.";
  renderAuthoringPreview(lesson);
}

function renderResponseAnalysis(analysis) {
  stateEls.responseScore.textContent = `score ${meter(analysis.score)} | keyword coverage ${analysis.keyword_hits}/${analysis.keyword_total} (${meter(analysis.coverage)})`;
  stateEls.responseFeedback.textContent = `${analysis.feedback} Calm alignment ${meter(analysis.calm_alignment)} | inquiry alignment ${meter(analysis.inquiry_alignment)}.`;
  renderStack(
    stateEls.responseDimensions,
    analysis.dimension_scores || [],
    (dimension) => `<strong>${dimension.label}</strong><div>score ${meter(dimension.score)} | weight ${meter(dimension.weight)}</div><div>${dimension.guidance}</div>`,
  );
}

function renderStats(state) {
  stateEls.tick.textContent = state.tick;
  stateEls.consensus.textContent = meter(state.hub_consensus);
  stateEls.knowledge.textContent = meter(state.mean_knowledge);
  stateEls.reflection.textContent = meter(state.mean_reflection);
  stateEls.coherence.textContent = meter(state.mean_coherence);
  stateEls.friction.textContent = meter(state.friction);
  renderLessonPanel(state);
  renderLessonFlow(state.lesson_flow);
  renderStudentHistory(activeStudentProfile());
  syncNarrativeToLessonState(state);

  stateEls.habitats.innerHTML = "";
  state.habitats.forEach((habitat) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = `
      <strong>${habitat.habitat_id}</strong>
      <div>stability ${meter(habitat.stability)} | nutrient ${meter(habitat.nutrient)}</div>
      <div>complexity ${meter(habitat.complexity)} | chemistry ${meter(habitat.chemistry)}</div>
      <div>biology ${meter(habitat.biology)} | physics ${meter(habitat.physics)}</div>
    `;
    stateEls.habitats.appendChild(node);
  });

  stateEls.cohort.innerHTML = "";
  state.agents.slice(0, 8).forEach((agent) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = `
      <strong>${agent.agent_id}</strong>
      <div>${agent.lifecycle_stage} | ${agent.specialization}</div>
      <div>knowledge ${meter(agent.knowledge)} | trust ${meter(agent.trust)} | stress ${meter(agent.stress)}</div>
    `;
    stateEls.cohort.appendChild(node);
  });
}

function renderRegistry(registry) {
  stateEls.registry.innerHTML = "";
  registry.equations.forEach((equation) => {
    const node = document.createElement("div");
    node.className = "item";
    node.innerHTML = `<strong>${equation.key}</strong><div>${equation.expression}</div><div>${equation.description}</div>`;
    stateEls.registry.appendChild(node);
  });
}

function drawFeed() {
  if (!liveState) {
    return;
  }

  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "rgba(138,174,163,0.12)");
  gradient.addColorStop(1, "rgba(203,169,108,0.07)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  const habitats = liveState.habitats;
  const agents = liveState.agents;
  const orbitY = height * 0.56;
  const baseRadius = Math.min(width, height) * 0.24;
  const animationScale = liveState.lesson_flow?.animation_scale ?? 1;
  const wave = Math.sin((liveState.tick || 0) * 0.35) * 6 * animationScale;

  ctx.strokeStyle = "rgba(80, 104, 96, 0.16)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.arc(width / 2, orbitY, baseRadius + 24 + wave, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = "rgba(50, 67, 63, 0.86)";
  ctx.font = "13px Consolas";
  ctx.fillText(liveState.dataset_title, 28, 28);
  if (activeLesson?.title) {
    ctx.fillText(activeLesson.title, 28, 48);
  }

  habitats.forEach((habitat, index) => {
    const angle = (Math.PI * 2 * index) / habitats.length - Math.PI / 2;
    const x = width / 2 + Math.cos(angle) * baseRadius;
    const y = orbitY + Math.sin(angle) * baseRadius * 0.68;
    const intensity = 0.28 + habitat.nutrient * 0.32;

    ctx.beginPath();
    ctx.fillStyle = `rgba(138,174,163,${intensity})`;
    ctx.arc(x, y, 18 + habitat.complexity * 24, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "rgba(80, 104, 96, 0.22)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(x, y, 30 + habitat.stability * 16, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = "rgba(50, 67, 63, 0.88)";
    ctx.font = "12px Consolas";
    ctx.fillText(habitat.habitat_id, x - 28, y + 4);
  });

  agents.forEach((agent, index) => {
    const habitatIndex = habitats.findIndex((habitat) => habitat.habitat_id === agent.habitat_id);
    const angle = (Math.PI * 2 * habitatIndex) / habitats.length - Math.PI / 2;
    const x = width / 2 + Math.cos(angle) * baseRadius + ((index % 4) - 1.5) * 18;
    const y = orbitY + Math.sin(angle) * baseRadius * 0.68 + ((index % 3) - 1) * 20 + Math.sin((liveState.tick + index) * 0.42) * 3;
    const size = 6 + agent.knowledge * 10;

    ctx.fillStyle = `rgba(203,169,108,${0.24 + agent.awareness * 0.34})`;
    ctx.fillRect(x - size / 2, y - size / 2, size, size);
  });

  const chartLeft = 48;
  const chartBottom = 84;
  const chartWidth = width - 96;
  const metrics = [
    ["consensus", liveState.hub_consensus, "#8aaea3"],
    ["knowledge", liveState.mean_knowledge, "#cba96c"],
    ["reflection", liveState.mean_reflection, "#a7b8b1"],
    ["coherence", liveState.mean_coherence, "#9b8571"],
  ];

  metrics.forEach(([label, value, color], index) => {
    const x = chartLeft + index * (chartWidth / metrics.length) + 28;
    const barHeight = value * 120;
    ctx.fillStyle = color;
    ctx.fillRect(x, chartBottom + 120 - barHeight, 42, barHeight);
    ctx.fillStyle = "rgba(50, 67, 63, 0.8)";
    ctx.font = "12px Consolas";
    ctx.fillText(label, x - 6, chartBottom + 142);
  });
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  return response.json();
}

async function refreshState() {
  liveState = await fetchJson("/api/state");
  syncActiveLessonFromState(liveState);
  renderStats(liveState);
  renderActivity();
  drawFeed();
}

async function loadRegistry() {
  const equationRegistry = await fetchJson("/api/registry");
  renderRegistry(equationRegistry);
}

async function loadDataset() {
  const datasetMeta = await fetchJson("/api/dataset");
  stateEls.datasetTitle.textContent = `${datasetMeta.title} (${datasetMeta.agent_count} agents / ${datasetMeta.habitat_count} habitats)`;
  stateEls.datasetNote.textContent = datasetMeta.note;
}

async function loadLessons() {
  lessonLibrary = await fetchJson("/api/lessons");
  baseLessonLibrary = deepClone(lessonLibrary);
  stateEls.lessonLibraryNote.textContent = lessonLibrary.note || "";
  renderLessonOptions();
  activeLesson = lessonLibrary.lessons?.[0] ?? null;
  if (activeLesson) {
    controls.lessonSelect.value = activeLesson.lesson_id;
    applyLessonDirective(activeLesson);
    resetLessonRuntime(activeLesson);
    resetNarrativeWindow(activeLesson);
    populateAuthoringStudio(activeLesson);
    renderLessonPanel({ lesson: activeLesson, lesson_mastery: [], mastery_overview: 0, lesson_depth: activeLesson.depth || { depth_score: 0 } });
    renderActivity();
  }
}

async function loadAnimationLibrary() {
  animationLibrary = await fetchJson("/api/animations");
  renderAuthorAnimationPicker(activeLesson?.animation_ids || []);
  renderAnimationGallery(activeLesson, currentActivity());
}

async function loadCourse() {
  const course = await fetchJson("/api/course");
  renderCoursePanel(course);
}

async function loadAssets() {
  const assetManifest = await fetchJson("/api/assets");
  assetEls.planetCore.src = assetManifest.planet_core;
  assetEls.glyphUpper.src = assetManifest.glyph_upper;
  assetEls.glyphLower.src = assetManifest.glyph_lower;
  assetEls.glyphSymbols.src = assetManifest.glyph_symbols;
  assetEls.streamMap.src = assetManifest.stream_map;
  assetEls.nodeSheet.src = assetManifest.node_sheet;
  assetEls.avatarSheet.src = assetManifest.avatar_sheet;
  assetEls.signalSheet.src = assetManifest.signal_sheet;
}

async function stepSimulation(stepsOverride = null) {
  liveState = await fetchJson("/api/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      steps: Number(stepsOverride ?? controls.steps.value),
      lesson: activeLesson,
      course: buildCoursePayload(true),
      directive: directivePayload(),
    }),
  });
  syncActiveLessonFromState(liveState);
  renderStats(liveState);
  renderActivity();
  drawFeed();
  scheduleAutoRun();
}

async function resetSimulation() {
  liveState = await fetchJson("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seed: 11, agent_count: 18, habitat_count: 4, lesson: activeLesson, course: buildCoursePayload(true) }),
  });
  syncActiveLessonFromState(liveState);
  renderStats(liveState);
  renderActivity();
  drawFeed();
  scheduleAutoRun();
}

async function scoreResponse() {
  const analysisPayload = await fetchJson("/api/respond", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      lesson: activeLesson,
      course: buildCoursePayload(true),
      student_id: controls.studentSelect.value || courseState?.active_student_id || "",
      response: stateEls.responseInput.value,
    }),
  });
  renderResponseAnalysis(analysisPayload.analysis);
  if (analysisPayload.history && courseState) {
    const student = activeStudentProfile();
    if (student) {
      const history = student.lesson_history || [];
      const existingIndex = history.findIndex((entry) => entry.lesson_id === analysisPayload.history.lesson_id);
      if (existingIndex >= 0) {
        history[existingIndex] = analysisPayload.history;
      } else {
        history.push(analysisPayload.history);
      }
      renderStudentHistory(student);
    }
  }
}

async function saveCourseSetup(includeCurrentStudent = false) {
  const payload = buildCoursePayload(includeCurrentStudent);
  courseState = await fetchJson("/api/course/setup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  renderCoursePanel(courseState);
}

async function generateStudentNote() {
  const workingCourse = buildCoursePayload(true);
  const studentId = workingCourse.active_student_id || workingCourse.students?.[0]?.student_id;
  if (!studentId) {
    renderStudentNote(null);
    stateEls.studentNoteOutput.textContent = "Create and save a student profile first.";
    return;
  }
  const note = await fetchJson("/api/student-note", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: studentId, lesson: activeLesson, course: workingCourse }),
  });
  courseState = await fetchJson("/api/course");
  renderCoursePanel(courseState);
  renderStudentNote(note);
}

function downloadCourseSetup() {
  const payload = {
    course: buildCoursePayload(true),
    exported_from: "CogniNeueroHub",
    version: 1,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${slugify(payload.course.title || "course-setup") || "course-setup"}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function stopAutoRun() {
  if (autoTimer) {
    clearTimeout(autoTimer);
    autoTimer = null;
  }
  controls.toggleAuto.textContent = "Auto run";
}

function scheduleAutoRun() {
  if (!autoTimer) {
    return;
  }
  clearTimeout(autoTimer);
  const interval = liveState?.lesson_flow?.auto_run_interval_ms ?? 1200;
  autoTimer = setTimeout(async () => {
    const steps = liveState?.lesson_flow?.recommended_step_count ?? Number(controls.steps.value);
    await stepSimulation(steps);
  }, interval);
}

async function importCourseSetupFromFile(file) {
  if (!file) {
    return;
  }
  const text = await file.text();
  const parsed = JSON.parse(text);
  courseState = await fetchJson("/api/course/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parsed.course || parsed),
  });
  renderCoursePanel(courseState);
  renderStudentNote(null);
}

controls.lessonSelect.addEventListener("change", () => {
  const nextLesson = findLessonById(controls.lessonSelect.value) || activeLesson;
  applyLessonDirective(nextLesson);
  resetLessonRuntime(nextLesson);
  resetNarrativeWindow(nextLesson);
  populateAuthoringStudio(nextLesson);
  renderLessonPanel({ lesson: nextLesson, lesson_mastery: [], mastery_overview: 0, lesson_depth: nextLesson.depth || { depth_score: 0 } });
  renderActivity();
});

controls.applyLessonAuthoring.addEventListener("click", applyLessonAuthoring);
controls.resetLessonAuthoring.addEventListener("click", restoreBaseLesson);
controls.exportAuthoredLesson.addEventListener("click", exportAuthoredLesson);

controls.studentSelect.addEventListener("change", () => {
  if (!courseState) {
    return;
  }
  courseState.active_student_id = controls.studentSelect.value;
  populateStudentForm(activeStudentProfile());
  renderStudentHistory(activeStudentProfile());
});

controls.saveCourseSetup.addEventListener("click", async () => {
  await saveCourseSetup(false);
});

controls.saveStudentProfile.addEventListener("click", async () => {
  await saveCourseSetup(true);
});

controls.exportCourseSetup.addEventListener("click", downloadCourseSetup);
controls.importCourseSetup.addEventListener("click", () => {
  controls.courseImportInput.click();
});
controls.courseImportInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  await importCourseSetupFromFile(file);
  controls.courseImportInput.value = "";
});

controls.generateStudentNote.addEventListener("click", generateStudentNote);
controls.speakStudentNote.addEventListener("click", speakStudentNote);
controls.stopStudentNote.addEventListener("click", stopSpeechPlayback);

controls.loadLesson.addEventListener("click", async () => {
  if (!activeLesson && lessonLibrary?.lessons?.length) {
    activeLesson = lessonLibrary.lessons[0];
  }
  applyLessonDirective(activeLesson);
  resetPaceRuntime();
  resetLessonRuntime(activeLesson);
  await resetSimulation();
});

controls.scoreResponse.addEventListener("click", scoreResponse);
controls.stepOnce.addEventListener("click", stepSimulation);
controls.reset.addEventListener("click", async () => {
  resetPaceRuntime();
  resetLessonRuntime(activeLesson, activeActivityIndex);
  await resetSimulation();
});
controls.previousActivity.addEventListener("click", () => {
  activeActivityIndex = Math.max(0, activeActivityIndex - 1);
  activityStartedAt = performance.now();
  ensureActivitySession();
  if (narrativeAutoMode) {
    syncNarrativeToLessonState(liveState || { tick: 0, mastery_overview: 0 });
  }
  renderActivity();
});
controls.nextActivity.addEventListener("click", () => {
  activeActivityIndex = Math.min(getActivities(activeLesson).length - 1, activeActivityIndex + 1);
  activityStartedAt = performance.now();
  ensureActivitySession();
  if (narrativeAutoMode) {
    syncNarrativeToLessonState(liveState || { tick: 0, mastery_overview: 0 });
  }
  renderActivity();
});
controls.narrativeBack.addEventListener("click", () => {
  activeNarrativeIndex = Math.max(0, activeNarrativeIndex - 1);
  renderNarrativeWindow();
});
controls.narrativeNext.addEventListener("click", () => {
  advanceNarrativeWindow();
});
controls.narrativeAuto.addEventListener("click", () => {
  narrativeAutoMode = !narrativeAutoMode;
  if (narrativeAutoMode) {
    syncNarrativeToLessonState(liveState || { tick: 0, mastery_overview: 0 });
  }
  renderNarrativeWindow();
});
controls.toggleAuto.addEventListener("click", () => {
  if (autoTimer) {
    stopAutoRun();
    return;
  }
  controls.toggleAuto.textContent = "Pause";
  autoTimer = setTimeout(() => {}, 0);
  scheduleAutoRun();
});

window.addEventListener("resize", drawFeed);
if ("speechSynthesis" in window) {
  window.speechSynthesis.addEventListener("voiceschanged", syncAvailableVoices);
}

async function init() {
  syncAvailableVoices();
  resetPaceRuntime();
  await Promise.all([loadRegistry(), loadDataset(), loadAssets(), loadLessons(), loadAnimationLibrary(), loadCourse()]);
  if (activeLesson) {
    await resetSimulation();
    return;
  }
  await refreshState();
}

init();
