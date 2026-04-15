package com.driptech.skulldummy

import android.graphics.BitmapFactory
import android.graphics.Rect
import android.media.MediaPlayer
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.driptech.skulldummy.ui.theme.SkullDummyTheme
import kotlinx.coroutines.delay
import kotlin.math.max
import kotlin.random.Random

private enum class BossMode {
    Idle,
    Advance,
    Combo,
}

private data class QtePrompt(
    val action: String,
    val response: String,
    val reward: Int,
    val penalty: Int,
)

private val qtePrompts = listOf(
    QtePrompt("Blade flare", "SLASH", 22, 12),
    QtePrompt("Skull feint", "GUARD", 18, 10),
    QtePrompt("Soul drag", "DODGE", 16, 9),
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SkullDummyTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    SkullDummyApp()
                }
            }
        }
    }
}

@Composable
private fun SkullDummyApp() {
    val context = LocalContext.current
    var playerHealth by remember { mutableIntStateOf(100) }
    var bossHealth by remember { mutableIntStateOf(100) }
    var zoneIndex by remember { mutableIntStateOf(0) }
    var gearCount by remember { mutableIntStateOf(2) }
    var relicCharge by remember { mutableFloatStateOf(0.35f) }
    var bossMode by remember { mutableStateOf(BossMode.Idle) }
    var promptIndex by remember { mutableIntStateOf(0) }
    var narratorLine by remember { mutableStateOf("The soul tether crackles. Cross the skull plain and strike on rhythm.") }
    var comboCount by remember { mutableIntStateOf(0) }
    var qteWindowOpen by remember { mutableStateOf(false) }
    var bossFrameTick by remember { mutableIntStateOf(0) }

    val prompt = qtePrompts[promptIndex]
    val encounterResolved = playerHealth <= 0 || bossHealth <= 0
    val encounterTitle = when {
        bossHealth <= 0 -> "Blunin broke first"
        playerHealth <= 0 -> "Skulldummy collapsed"
        else -> "Skull Plain // Zone ${zoneIndex + 1}"
    }

    DisposableEffect(Unit) {
        val music = MediaPlayer.create(context, R.raw.skulldummy_idtech_music)
        music?.isLooping = true
        runCatching { music?.start() }
        onDispose {
            music?.stop()
            music?.release()
        }
    }

    LaunchedEffect(encounterResolved) {
        while (!encounterResolved) {
            delay(160L)
            bossFrameTick += 1
            if (bossFrameTick % 10 == 0) {
                bossMode = when (Random.nextInt(3)) {
                    0 -> BossMode.Idle
                    1 -> BossMode.Advance
                    else -> BossMode.Combo
                }
                qteWindowOpen = true
                promptIndex = Random.nextInt(qtePrompts.size)
                narratorLine = when (bossMode) {
                    BossMode.Idle -> "The soul tether narrows. Read the pause before the cut."
                    BossMode.Advance -> "Blunin advances across the dust sheet. Answer fast."
                    BossMode.Combo -> "Combo pattern incoming. Match the whisper, not the blade."
                }
            }
            if (bossFrameTick % 10 == 4 && qteWindowOpen) {
                qteWindowOpen = false
                playerHealth = max(0, playerHealth - prompt.penalty)
                narratorLine = "You hesitated. The tether ate ${prompt.penalty} health."
                comboCount = 0
            }
            relicCharge = (relicCharge + 0.015f).coerceAtMost(1f)
        }
    }

    fun playQteSfx() {
        val player = MediaPlayer.create(context, R.raw.qte_comic_engine_sfx)
        player?.setOnCompletionListener {
            it.release()
        }
        runCatching { player?.start() }
    }

    fun resolvePrompt(answer: String) {
        if (encounterResolved || !qteWindowOpen) {
            narratorLine = "The opening passed. Watch the stance and wait for the next fracture."
            return
        }
        playQteSfx()
        qteWindowOpen = false
        if (answer == prompt.response) {
            bossHealth = max(0, bossHealth - prompt.reward)
            comboCount += 1
            gearCount = minOf(5, gearCount + 1)
            relicCharge = (relicCharge + 0.12f).coerceAtMost(1f)
            narratorLine = "Clean hit. ${prompt.reward} damage through the soul seam."
        } else {
            playerHealth = max(0, playerHealth - prompt.penalty)
            comboCount = 0
            narratorLine = "Wrong read. Blunin answered with ${prompt.penalty} damage."
        }
    }

    fun stepZone() {
        zoneIndex = (zoneIndex + 1) % 3
        gearCount = minOf(5, gearCount + 1)
        relicCharge = (relicCharge + 0.18f).coerceAtMost(1f)
        narratorLine = "You crossed into a new skull district. The tether strengthened."
    }

    fun useRelicBurst() {
        if (relicCharge < 0.5f || encounterResolved) {
            narratorLine = "The relic bundle is not charged enough yet."
            return
        }
        playQteSfx()
        relicCharge = 0.1f
        bossHealth = max(0, bossHealth - 14)
        narratorLine = "Relic burst landed. The dust field peeled back for a moment."
    }

    fun resetEncounter() {
        playerHealth = 100
        bossHealth = 100
        zoneIndex = 0
        gearCount = 2
        relicCharge = 0.35f
        bossMode = BossMode.Idle
        promptIndex = 0
        narratorLine = "The tether rethreads itself. One more walk across the skull plain."
        comboCount = 0
        qteWindowOpen = false
        bossFrameTick = 0
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B0B0D))
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            Card(shape = RoundedCornerShape(24.dp)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFF11141A))
                        .padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("SKULLDUMMY // ANDROID SLICE", color = Color(0xFFF4E3B4), style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Black)
                    Text(encounterTitle, color = Color(0xFF9CD7F0), style = MaterialTheme.typography.titleMedium)
                    Text(
                        "Explore the skull plain, charge relics, and beat Blunin in short QTE windows recovered from the D-drive art set.",
                        color = Color(0xFFE9EDF7),
                    )
                }
            }
        }
        item {
            BossArena(
                bossMode = bossMode,
                tick = bossFrameTick,
                qteWindowOpen = qteWindowOpen,
                zoneIndex = zoneIndex,
            )
        }
        item {
            CombatStatus(
                playerHealth = playerHealth,
                bossHealth = bossHealth,
                gearCount = gearCount,
                relicCharge = relicCharge,
                comboCount = comboCount,
                narratorLine = narratorLine,
                prompt = prompt,
                qteWindowOpen = qteWindowOpen,
            )
        }
        item {
            RelicStrip(gearCount = gearCount)
        }
        item {
            Card(shape = RoundedCornerShape(24.dp)) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(Color(0xFF161B22))
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text("Combat Inputs", color = Color(0xFFF7ECD2), style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Button(onClick = { resolvePrompt("SLASH") }) { Text("SLASH") }
                        Button(onClick = { resolvePrompt("GUARD") }) { Text("GUARD") }
                        Button(onClick = { resolvePrompt("DODGE") }) { Text("DODGE") }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Button(onClick = ::stepZone, enabled = !encounterResolved) { Text("Step Zone") }
                        Button(onClick = ::useRelicBurst, enabled = !encounterResolved) { Text("Relic Burst") }
                        Button(onClick = ::resetEncounter) { Text("Reset") }
                    }
                }
            }
        }
    }
}

@Composable
private fun BossArena(
    bossMode: BossMode,
    tick: Int,
    qteWindowOpen: Boolean,
    zoneIndex: Int,
) {
    val backgroundRes = when (zoneIndex) {
        0 -> R.drawable.blunin_bg_layer_1
        1 -> R.drawable.blunin_bg_layer_2
        else -> R.drawable.blunin_bg_layer_3
    }
    Card(shape = RoundedCornerShape(24.dp)) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
                .background(Color.Black),
        ) {
            Image(
                painter = painterResource(backgroundRes),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize(),
            )
            AnimatedBoss(bossMode = bossMode, tick = tick)
            if (qteWindowOpen) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .padding(top = 12.dp)
                        .background(Color(0xCC8B1018), RoundedCornerShape(16.dp))
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                ) {
                    Text("QTE WINDOW", color = Color.White, fontWeight = FontWeight.Black)
                }
            }
        }
    }
}

@Composable
private fun AnimatedBoss(bossMode: BossMode, tick: Int) {
    val context = LocalContext.current
    val frameSet = when (bossMode) {
        BossMode.Idle -> R.drawable.blunin_idle_sheet
        BossMode.Advance -> R.drawable.blunin_walk_sheet
        BossMode.Combo -> R.drawable.blunin_attack_sheet
    }
    val bitmap = remember(frameSet) {
        BitmapFactory.decodeResource(context.resources, frameSet)
    }
    Canvas(modifier = Modifier.fillMaxSize()) {
        val frameWidth = bitmap.width / 6
        val frameIndex = (tick / 2) % 6
        val sourceRect = Rect(frameIndex * frameWidth, 0, (frameIndex + 1) * frameWidth, bitmap.height)
        val sway = when (bossMode) {
            BossMode.Idle -> 0f
            BossMode.Advance -> 18f
            BossMode.Combo -> 30f
        }
        val destinationRect = android.graphics.Rect(
            (size.width * 0.4f + sway).toInt(),
            (size.height * 0.18f).toInt(),
            (size.width * 0.78f + sway).toInt(),
            (size.height * 0.92f).toInt(),
        )
        drawIntoCanvas { canvas ->
            canvas.nativeCanvas.drawBitmap(bitmap, sourceRect, destinationRect, null)
        }
        val floorY = size.height * 0.82f
        drawLine(
            color = Color(0x66F3D8A5),
            start = Offset(size.width * 0.12f, floorY),
            end = Offset(size.width * 0.88f, floorY),
            strokeWidth = 3.dp.toPx(),
        )
    }
}

@Composable
private fun CombatStatus(
    playerHealth: Int,
    bossHealth: Int,
    gearCount: Int,
    relicCharge: Float,
    comboCount: Int,
    narratorLine: String,
    prompt: QtePrompt,
    qteWindowOpen: Boolean,
) {
    Card(shape = RoundedCornerShape(24.dp)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFF171717))
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            StatMeter("Skulldummy Integrity", playerHealth / 100f, Color(0xFF7AD3A1), "$playerHealth / 100")
            StatMeter("Blunin Integrity", bossHealth / 100f, Color(0xFFE77373), "$bossHealth / 100")
            StatMeter("Relic Charge", relicCharge, Color(0xFF83C9FF), "${(relicCharge * 100).toInt()}%")
            Text("Gear nodes: $gearCount | Combo: $comboCount", color = Color(0xFFE5E5E5))
            Text(narratorLine, color = Color(0xFFF4E3B4))
            if (qteWindowOpen) {
                Text("Answer now: ${prompt.action} -> ${prompt.response}", color = Color(0xFF9CD7F0), fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun StatMeter(label: String, progress: Float, color: Color, valueLabel: String) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(label, color = Color.White, fontWeight = FontWeight.SemiBold)
            Text(valueLabel, color = Color(0xFFD6D6D6))
        }
        LinearProgressIndicator(
            progress = { progress.coerceIn(0f, 1f) },
            modifier = Modifier.fillMaxWidth(),
            color = color,
            trackColor = Color(0xFF353535),
        )
    }
}

@Composable
private fun RelicStrip(gearCount: Int) {
    Card(shape = RoundedCornerShape(24.dp)) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color(0xFF12161D))
                .padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Relics", color = Color(0xFFF4E3B4), fontWeight = FontWeight.Bold)
            repeat(gearCount.coerceAtMost(5)) { index ->
                Image(
                    painter = painterResource(
                        when (index) {
                            0 -> R.drawable.skull_relic_1
                            1 -> R.drawable.skull_relic_2
                            2 -> R.drawable.skull_relic_3
                            3 -> R.drawable.skull_relic_4
                            else -> R.drawable.skull_relic_5
                        },
                    ),
                    contentDescription = null,
                    modifier = Modifier.size(34.dp),
                )
            }
            Spacer(modifier = Modifier.weight(1f))
            Text("Recovered from the skull plain", color = Color(0xFFB0BECC))
        }
    }
}