package com.driptech.pocode.ui.game

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.driptech.pocode.campaign.GameResult
import com.driptech.pocode.campaign.LessonInstance
import com.driptech.pocode.campaign.LessonResult
import com.driptech.pocode.campaign.MiniGamePrompt
import com.driptech.pocode.campaign.MiniGameType
import kotlin.random.Random

@Composable
fun MiniGameScreen(
    lessonInstance: LessonInstance,
    seedHash: Int,
    onLessonFinished: (LessonResult) -> Unit,
    onExit: () -> Unit,
) {
    val games = lessonInstance.games
    if (games.isEmpty()) {
        onLessonFinished(LessonResult(lessonInstance.lesson.id, emptyList()))
        return
    }

    var currentIndex by remember { mutableIntStateOf(0) }
    val results = remember { mutableStateListOf<GameResult>() }
    var feedbackState by remember { mutableStateOf<FeedbackState?>(null) }

    val finished = currentIndex >= games.size

    if (finished) {
        ResultsSummary(
            lessonTitle = lessonInstance.lesson.title,
            results = results.toList(),
            onContinue = {
                onLessonFinished(LessonResult(lessonInstance.lesson.id, results.toList()))
            },
            onExit = onExit,
        )
    } else {
        val game = games[currentIndex]
        val shuffledOptions = remember(game.id, seedHash) {
            game.options.shuffled(Random(game.id.hashCode() xor seedHash))
        }

        GamePromptView(
            game = game,
            shuffledOptions = shuffledOptions,
            questionNumber = currentIndex + 1,
            totalQuestions = games.size,
            feedbackState = feedbackState,
            onAnswer = { chosen ->
                if (feedbackState != null) return@GamePromptView
                val correct = chosen == game.correctAnswer
                val result = GameResult(
                    gameId = game.id,
                    conceptId = game.primaryConceptId,
                    correct = correct,
                    chosenAnswer = chosen,
                )
                results.add(result)
                feedbackState = FeedbackState(
                    correct = correct,
                    chosenAnswer = chosen,
                    correctAnswer = game.correctAnswer,
                    hint = game.hint,
                )
            },
            onNext = {
                feedbackState = null
                currentIndex++
            },
        )
    }
}

private enum class FeedbackColor { Neutral, Correct, Wrong }

private data class FeedbackState(
    val correct: Boolean,
    val chosenAnswer: String,
    val correctAnswer: String,
    val hint: String,
)

@Composable
private fun GamePromptView(
    game: MiniGamePrompt,
    shuffledOptions: List<String>,
    questionNumber: Int,
    totalQuestions: Int,
    feedbackState: FeedbackState?,
    onAnswer: (String) -> Unit,
    onNext: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF3E9D2))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            LinearProgressIndicator(
                progress = { questionNumber.toFloat() / totalQuestions.toFloat() },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(4.dp)),
                color = Color(0xFF2A9D8F),
                trackColor = Color(0xFFE6DDD0),
            )
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(
                    "$questionNumber / $totalQuestions",
                    style = MaterialTheme.typography.labelLarge,
                    color = Color(0xFF57707A),
                )
                Text(
                    gameTypeLabel(game.type),
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    color = gameTypeColor(game.type),
                )
            }
        }

        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFF12343B))
                        .padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(
                        game.prompt,
                        style = MaterialTheme.typography.titleMedium,
                        color = Color(0xFFF7F1E3),
                        fontWeight = FontWeight.Bold,
                    )
                    if (game.reinforcement) {
                        Text(
                            "Reinforcement round",
                            style = MaterialTheme.typography.labelSmall,
                            color = Color(0xFFFFD27F),
                        )
                    }
                }
            }
        }

        itemsIndexed(shuffledOptions) { _, option ->
            val feedbackColor = when {
                feedbackState == null -> FeedbackColor.Neutral
                option == feedbackState.correctAnswer -> FeedbackColor.Correct
                option == feedbackState.chosenAnswer && !feedbackState.correct -> FeedbackColor.Wrong
                else -> FeedbackColor.Neutral
            }

            val bgColor by animateColorAsState(
                targetValue = when (feedbackColor) {
                    FeedbackColor.Correct -> Color(0xFF2A9D8F)
                    FeedbackColor.Wrong -> Color(0xFFE76F51)
                    FeedbackColor.Neutral -> Color(0xFFFFFCF3)
                },
                label = "optionBg",
            )
            val textColor = when (feedbackColor) {
                FeedbackColor.Correct, FeedbackColor.Wrong -> Color.White
                FeedbackColor.Neutral -> Color(0xFF2F3E46)
            }
            val borderColor = when (feedbackColor) {
                FeedbackColor.Correct -> Color(0xFF1B7A6E)
                FeedbackColor.Wrong -> Color(0xFFC44536)
                FeedbackColor.Neutral -> Color(0xFFDBD7CC)
            }

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .border(2.dp, borderColor, RoundedCornerShape(14.dp))
                    .background(bgColor)
                    .clickable(enabled = feedbackState == null) { onAnswer(option) }
                    .padding(16.dp),
            ) {
                Text(option, color = textColor, fontWeight = FontWeight.Medium)
            }
        }

        if (feedbackState != null) {
            item {
                Card(shape = RoundedCornerShape(16.dp)) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(if (feedbackState.correct) Color(0xFFD4EDDA) else Color(0xFFF8D7DA))
                            .padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        Text(
                            if (feedbackState.correct) "Correct!" else "Not quite.",
                            fontWeight = FontWeight.Bold,
                            color = if (feedbackState.correct) Color(0xFF155724) else Color(0xFF721C24),
                        )
                        if (!feedbackState.correct) {
                            Text("Hint: ${feedbackState.hint}", color = Color(0xFF856404))
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Button(onClick = onNext, modifier = Modifier.fillMaxWidth()) {
                            Text(if (feedbackState.correct) "Next" else "Try again next time")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ResultsSummary(
    lessonTitle: String,
    results: List<GameResult>,
    onContinue: () -> Unit,
    onExit: () -> Unit,
) {
    val correct = results.count { it.correct }
    val total = results.size
    val passed = total > 0 && correct.toFloat() / total >= 0.6f

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF3E9D2))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        item {
            Card(shape = RoundedCornerShape(24.dp)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(if (passed) Color(0xFF2C3930) else Color(0xFF3B1F2B))
                        .padding(24.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Text(
                        if (passed) "Lesson Complete" else "Keep Practicing",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Black,
                        color = Color(0xFFF7F1E3),
                    )
                    Text(
                        lessonTitle,
                        style = MaterialTheme.typography.titleMedium,
                        color = Color(0xFFFFD27F),
                    )
                    Text(
                        "$correct / $total correct",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = if (passed) Color(0xFF2A9D8F) else Color(0xFFE76F51),
                        textAlign = TextAlign.Center,
                    )
                    LinearProgressIndicator(
                        progress = { if (total > 0) correct.toFloat() / total else 0f },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(10.dp)
                            .clip(RoundedCornerShape(5.dp)),
                        color = if (passed) Color(0xFF2A9D8F) else Color(0xFFE76F51),
                        trackColor = Color(0xFF44544A),
                    )
                }
            }
        }

        item {
            Card(shape = RoundedCornerShape(20.dp)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFFFFFCF3))
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(
                        "Breakdown",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF1E2B2F),
                    )
                    results.forEachIndexed { index, result ->
                        val icon = if (result.correct) "✓" else "✗"
                        val color = if (result.correct) Color(0xFF2A9D8F) else Color(0xFFE76F51)
                        Text(
                            "$icon  ${index + 1}. ${result.conceptId}",
                            color = color,
                            fontWeight = FontWeight.Medium,
                        )
                    }
                }
            }
        }

        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Button(onClick = onContinue, modifier = Modifier.weight(1f)) {
                    Text(if (passed) "Continue" else "Move On")
                }
                Button(onClick = onExit, modifier = Modifier.weight(1f)) {
                    Text("Back to Map")
                }
            }
        }
    }
}

private fun gameTypeLabel(type: MiniGameType): String = when (type) {
    MiniGameType.Identify -> "IDENTIFY"
    MiniGameType.Match -> "MATCH"
    MiniGameType.Repair -> "REPAIR"
    MiniGameType.Assemble -> "ASSEMBLE"
    MiniGameType.Predict -> "PREDICT"
}

private fun gameTypeColor(type: MiniGameType): Color = when (type) {
    MiniGameType.Identify -> Color(0xFF2A9D8F)
    MiniGameType.Match -> Color(0xFF264653)
    MiniGameType.Repair -> Color(0xFFE76F51)
    MiniGameType.Assemble -> Color(0xFFE9C46A)
    MiniGameType.Predict -> Color(0xFF6A4C93)
}
