package com.driptech.pocode

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.driptech.pocode.campaign.AdaptiveLearningEngine
import com.driptech.pocode.campaign.CampaignBlueprint
import com.driptech.pocode.campaign.CampaignGenerator
import com.driptech.pocode.campaign.LessonInstance
import com.driptech.pocode.campaign.NodeKind
import com.driptech.pocode.campaign.PlayerProgress
import com.driptech.pocode.campaign.ProjectPresets
import com.driptech.pocode.campaign.ProjectRequest
import com.driptech.pocode.data.PocodeProgressStore
import com.driptech.pocode.ui.game.MiniGameScreen
import com.driptech.pocode.ui.theme.PocodeTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PocodeTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    PocodeWorkbenchApp()
                }
            }
        }
    }
}

@Composable
private fun PocodeWorkbenchApp() {
    val context = LocalContext.current
    val initialSaved = remember { PocodeProgressStore.load(context) }
    val initialRequest = initialSaved?.request ?: ProjectPresets.textToSpeechStarter
    val initialProgress = initialSaved?.progress ?: PlayerProgress()
    val initialBlueprint = remember(initialRequest) { CampaignGenerator.build(initialRequest) }

    var request by remember { mutableStateOf(initialRequest) }
    var progress by remember { mutableStateOf(initialProgress) }
    var status by remember {
        mutableStateOf(
            if (initialSaved == null) {
                "Using the text-to-speech starter preset for the restored Pocode launcher."
            } else {
                "Loaded saved Pocode campaign state."
            }
        )
    }
    var nodeIndex by remember { mutableIntStateOf(findStartingNode(initialBlueprint, initialProgress)) }
    var playingLesson by remember { mutableStateOf<LessonInstance?>(null) }

    val blueprint = remember(request) { CampaignGenerator.build(request) }
    val clampedNodeIndex = nodeIndex.coerceIn(0, blueprint.nodes.lastIndex.coerceAtLeast(0))
    val activeNode = blueprint.nodes.getOrNull(clampedNodeIndex)
    val lessonInstance = activeNode?.let { CampaignGenerator.lessonInstanceFor(blueprint, it, progress) }

    fun resetTo(requestValue: ProjectRequest, progressValue: PlayerProgress, note: String) {
        val nextBlueprint = CampaignGenerator.build(requestValue)
        request = requestValue
        progress = progressValue
        nodeIndex = findStartingNode(nextBlueprint, progressValue)
        playingLesson = null
        status = note
    }

    fun advanceNode() {
        if (blueprint.nodes.isEmpty()) {
            return
        }
        nodeIndex = (clampedNodeIndex + 1).coerceAtMost(blueprint.nodes.lastIndex)
    }

    val activePlaying = playingLesson
    if (activePlaying != null) {
        MiniGameScreen(
            lessonInstance = activePlaying,
            seedHash = request.seedWord.hashCode(),
            onLessonFinished = { result ->
                progress = AdaptiveLearningEngine.registerDetailedOutcome(progress, result)
                val verb = if (result.passed) "Cleared" else "Reviewed"
                status = "$verb '${activePlaying.lesson.title}': ${result.correctCount}/${result.totalCount} correct."
                playingLesson = null
                if (result.passed) advanceNode()
            },
            onExit = {
                playingLesson = null
            },
        )
        return
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF3E9D2))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Card(shape = RoundedCornerShape(24.dp)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFF12343B))
                        .padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("POCODE", color = Color(0xFFF7F1E3), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black)
                    Text(
                        "Adaptive campaign shell restored as a dedicated Pocode app module with no cross-project gameplay slice bundled into it.",
                        color = Color(0xFFD9E8E4),
                    )
                    Text(status, color = Color(0xFFFFD27F), style = MaterialTheme.typography.bodyMedium)
                }
            }
        }

        item {
            Card(shape = RoundedCornerShape(24.dp)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFFF7F1E3))
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text("Campaign Controls", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color(0xFF1E2B2F))
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Button(onClick = {
                            resetTo(
                                ProjectPresets.textToSpeechStarter,
                                PlayerProgress(),
                                "Started a fresh text-to-speech learning campaign.",
                            )
                        }) {
                            Text("Fresh TTS Run")
                        }
                        Button(onClick = {
                            val loaded = PocodeProgressStore.load(context)
                            if (loaded == null) {
                                status = "No saved Pocode state found on disk yet."
                            } else {
                                resetTo(loaded.request, loaded.progress, "Reloaded saved Pocode progress from disk.")
                            }
                        }) {
                            Text("Load Save")
                        }
                        Button(onClick = {
                            PocodeProgressStore.save(context, request, progress)
                            status = "Saved current request, progression, and remediation state."
                        }) {
                            Text("Save")
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Button(onClick = { nodeIndex = (clampedNodeIndex - 1).coerceAtLeast(0) }, enabled = clampedNodeIndex > 0) {
                            Text("Previous Node")
                        }
                        Button(onClick = ::advanceNode, enabled = clampedNodeIndex < blueprint.nodes.lastIndex) {
                            Text("Next Node")
                        }
                    }
                }
            }
        }

        item {
            RequestSummaryCard(request = request, blueprint = blueprint, progress = progress)
        }

        item {
            RouteCard(blueprint = blueprint, activeNodeIndex = clampedNodeIndex)
        }

        item {
            ActiveNodeCard(
                activeNodeTitle = activeNode?.title ?: "No node available",
                activeNodeSubtitle = activeNode?.subtitle ?: "The campaign generator did not produce any route nodes.",
                lessonInstance = lessonInstance,
                onPlayLesson = {
                    val lesson = lessonInstance ?: return@ActiveNodeCard
                    playingLesson = lesson
                },
                onNodeAction = {
                    val node = activeNode ?: return@ActiveNodeCard
                    when (node.kind) {
                        NodeKind.RestStop -> {
                            progress = CampaignGenerator.applyRestStop(progress, node)
                            status = "Applied ${node.title.lowercase()} and softened upcoming pacing."
                            advanceNode()
                        }
                        NodeKind.RewardCache -> {
                            val reward = "Theme Disk ${clampedNodeIndex + 1}"
                            progress = progress.copy(avatarInventory = (progress.avatarInventory + reward).distinct())
                            status = "Claimed $reward for the avatar inventory."
                            advanceNode()
                        }
                        NodeKind.Lesson, NodeKind.BossLesson -> {
                            status = "Tap 'Play Lesson' to start the interactive challenge."
                        }
                    }
                },
                activeNodeKind = activeNode?.kind,
            )
        }

        if (lessonInstance != null) {
            item {
                LessonPreviewCard(lessonInstance = lessonInstance)
            }
        }

        item {
            ProgressCard(progress = progress)
        }
    }
}

@Composable
private fun RequestSummaryCard(
    request: ProjectRequest,
    blueprint: CampaignBlueprint,
    progress: PlayerProgress,
) {
    Card(shape = RoundedCornerShape(24.dp)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFFFFFCF3))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Project Request", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color(0xFF1E2B2F))
            Text("Idea: ${request.projectIdea}", color = Color(0xFF2F3E46))
            Text("Language: ${request.language} | Level: ${request.learnerLevel} | Session: ${request.sessionLengthMinutes} min", color = Color(0xFF2F3E46))
            Text("Seed word: ${request.seedWord}", color = Color(0xFF2F3E46))
            Text(blueprint.compilerSummary, color = Color(0xFF57707A))
            LinearProgressIndicator(
                progress = { progress.recentAccuracy.coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth(),
                color = Color(0xFF2A9D8F),
                trackColor = Color(0xFFE6DDD0),
            )
        }
    }
}

@Composable
private fun RouteCard(blueprint: CampaignBlueprint, activeNodeIndex: Int) {
    Card(shape = RoundedCornerShape(24.dp)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFFDDE7C7))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Seeded Route", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color(0xFF223127))
            blueprint.nodes.forEachIndexed { index, node ->
                val selected = index == activeNodeIndex
                Text(
                    text = if (selected) "▶ ${node.title}" else "• ${node.title}",
                    color = if (selected) Color(0xFF0D5C63) else Color(0xFF334139),
                    fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
                )
            }
        }
    }
}

@Composable
private fun ActiveNodeCard(
    activeNodeTitle: String,
    activeNodeSubtitle: String,
    lessonInstance: LessonInstance?,
    activeNodeKind: NodeKind?,
    onPlayLesson: () -> Unit,
    onNodeAction: () -> Unit,
) {
    Card(shape = RoundedCornerShape(24.dp)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFF2C3930))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Active Node", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color(0xFFF5F5F0))
            Text(activeNodeTitle, style = MaterialTheme.typography.titleMedium, color = Color(0xFFFFD27F))
            Text(activeNodeSubtitle, color = Color(0xFFE5EFE7))
            if (lessonInstance != null) {
                Text(lessonInstance.pacingHint, color = Color(0xFFB8D8BA))
                Text(lessonInstance.remediationSummary, color = Color(0xFFB8D8BA))
                Text("${lessonInstance.games.size} challenges ready", color = Color(0xFFE1F0EC), style = MaterialTheme.typography.bodySmall)
                Button(onClick = onPlayLesson) {
                    Text("Play Lesson")
                }
            } else if (activeNodeKind != null) {
                Button(onClick = onNodeAction) {
                    Text(
                        when (activeNodeKind) {
                            NodeKind.RestStop -> "Apply Rest Stop"
                            NodeKind.RewardCache -> "Claim Reward"
                            NodeKind.Lesson, NodeKind.BossLesson -> "Hold"
                        }
                    )
                }
            }
        }
    }
}

@Composable
private fun LessonPreviewCard(lessonInstance: LessonInstance) {
    Card(shape = RoundedCornerShape(24.dp)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFFFFFCF3))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Lesson Deck Preview", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color(0xFF1E2B2F))
            Text(lessonInstance.lesson.title, color = Color(0xFF2F3E46), fontWeight = FontWeight.SemiBold)
            lessonInstance.games.take(5).forEach { game ->
                Text(
                    "${game.type.name}: ${game.prompt}",
                    color = Color(0xFF485E67),
                )
                Text(
                    "Best answer: ${game.correctAnswer}",
                    color = Color(0xFF6B7F86),
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

@Composable
private fun ProgressCard(progress: PlayerProgress) {
    Card(shape = RoundedCornerShape(24.dp)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFF12343B))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Player Progress", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = Color(0xFFF5F5F0))
            Text("Completed lessons: ${progress.completedLessonIds.size}", color = Color(0xFFE1F0EC))
            Text("Successes: ${progress.totalSuccesses} | Mistakes: ${progress.totalMistakes}", color = Color(0xFFE1F0EC))
            Text("Active rest relief nodes: ${progress.activeRestReliefNodes}", color = Color(0xFFE1F0EC))
            Text("Inventory: ${progress.avatarInventory.joinToString()}", color = Color(0xFFE1F0EC))
            if (progress.conceptMistakes.isNotEmpty()) {
                Text("Concept pressure: ${progress.conceptMistakes.entries.joinToString { "${it.key}=${it.value}" }}", color = Color(0xFFFFD27F))
            }
        }
    }
}

private fun findStartingNode(blueprint: CampaignBlueprint, progress: PlayerProgress): Int {
    val incompleteLessonIndex = blueprint.nodes.indexOfFirst { node ->
        val lessonId = node.lessonId
        lessonId != null && lessonId !in progress.completedLessonIds
    }
    return if (incompleteLessonIndex >= 0) incompleteLessonIndex else 0
}