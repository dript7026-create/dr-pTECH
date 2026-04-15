package {
    import flash.display.Bitmap;
    import flash.display.BitmapData;
    import flash.display.Graphics;
    import flash.display.Shape;
    import flash.display.Sprite;
    import flash.events.Event;
    import flash.events.KeyboardEvent;
    import flash.events.SampleDataEvent;
    import flash.media.Sound;
    import flash.media.SoundChannel;
    import flash.media.SoundTransform;
    import flash.text.TextField;
    import flash.text.TextFieldAutoSize;
    import flash.text.TextFormat;
    import flash.text.TextFormatAlign;
    import flash.ui.Keyboard;

    public class GameScript extends Sprite {
        private static const VIEW_W:int = 960;
        private static const VIEW_H:int = 540;
        private static const BG_W:int = 160;
        private static const BG_H:int = 90;
        private static const FRAME_RATE:Number = 60.0;
        private static const LANE_COUNT:int = 4;
        private static const STRIKE_Y:Number = 428.0;
        private static const HIT_WINDOW:Number = 34.0;
        private static const MISS_WINDOW:Number = 74.0;

        private var title:String;
        private var initialized:Boolean = false;

        private var backgroundData:BitmapData;
        private var backgroundBitmap:Bitmap;
        private var runwayLayer:Shape;
        private var cueLayer:Shape;
        private var enemyLayer:Shape;
        private var playerLayer:Shape;
        private var particleLayer:Shape;

        private var titleField:TextField;
        private var scoreField:TextField;
        private var comboField:TextField;
        private var wardrobeField:TextField;
        private var enemyField:TextField;
        private var helpField:TextField;
        private var lockField:TextField;
        private var systemField:TextField;

        private var cues:Array = [];
        private var particles:Array = [];
        private var keyDown:Object = {};

        private var laneCenters:Array = [388.0, 478.0, 568.0, 658.0];
        private var laneNames:Array = ["Head Flick", "Torso Pulse", "Hand Halo", "Foot Spark"];
        private var laneGlyphs:Array = ["Flick", "Pulse", "Halo", "Spark"];
        private var encounterTitles:Array = ["Prism Tail", "Glue Stall", "Spectrum Mote", "Ember Roll", "Luster Knot"];
        private var encounterArchetypes:Array = ["Prism Bloom", "Glue Braid", "Ember Choir", "Halo Scythe", "Luster Knot"];

        private var score:int = 0;
        private var combo:int = 0;
        private var beatIndex:int = 0;
        private var encounterIndex:int = 0;
        private var currentFrame:int = 0;
        private var outfitTier:int = 0;

        private var dressCharge:Number = 0.0;
        private var matterDisruption:Number = 0.14;
        private var emberence:Number = 0.18;
        private var spectralPulse:Number = 0.0;
        private var sparkleFlash:Number = 0.0;
        private var playerPoseAngle:Number = 0.0;
        private var targetPoseAngle:Number = 0.0;
        private var poseSpin:Number = 0.0;
        private var runwayPulse:Number = 0.0;
        private var finisherBloom:Number = 0.0;

        private var bpm:Number = 142.0;
        private var beatDuration:Number = 60.0 / 142.0;
        private var songTime:Number = 0.0;
        private var nextBeatTime:Number = 0.0;

        private var lockReady:Boolean = false;
        private var lockTimer:Number = 0.0;
        private var lockTargetAngle:Number = 0.0;
        private var lastCueHint:String = "Catch the lane hits and weave Sparkle into the outfit.";

        private var tutorialActive:Boolean = true;
        private var tutorialStep:int = 0;
        private var tutorialCueHits:int = 0;

        private var currentEnemy:LiteMiteState;

        private var sound:Sound;
        private var channel:SoundChannel;
        private var audioCursor:Number = 0.0;
        private var bassEnergy:Number = 0.0;
        private var snareSplash:Number = 0.0;
        private var hatEnergy:Number = 0.0;
        private var sparkleAudio:Number = 0.0;
        private var tailNoise:Number = 0.0;

        public function GameScript(projectTitle:String) {
            title = projectTitle;
            if (stage) {
                initialize();
            } else {
                addEventListener(Event.ADDED_TO_STAGE, onAddedToStage);
            }
        }

        private function onAddedToStage(event:Event):void {
            removeEventListener(Event.ADDED_TO_STAGE, onAddedToStage);
            initialize();
        }

        private function initialize():void {
            if (initialized) {
                return;
            }
            initialized = true;

            graphics.beginFill(0x000000, 0);
            graphics.drawRect(0, 0, VIEW_W, VIEW_H);
            graphics.endFill();

            backgroundData = new BitmapData(BG_W, BG_H, false, 0x070C14);
            backgroundBitmap = new Bitmap(backgroundData);
            backgroundBitmap.width = VIEW_W;
            backgroundBitmap.height = VIEW_H;
            addChild(backgroundBitmap);

            runwayLayer = new Shape();
            cueLayer = new Shape();
            enemyLayer = new Shape();
            playerLayer = new Shape();
            particleLayer = new Shape();

            addChild(runwayLayer);
            addChild(cueLayer);
            addChild(enemyLayer);
            addChild(playerLayer);
            addChild(particleLayer);

            buildHud();

            stage.addEventListener(KeyboardEvent.KEY_DOWN, onKeyDown);
            stage.addEventListener(KeyboardEvent.KEY_UP, onKeyUp);
            stage.focus = stage;

            spawnEncounter();
            refreshTutorialPrompt();
            if (!tutorialActive) {
                for (var preload:int = 0; preload < 3; preload++) {
                    spawnCue(preload);
                }
            }
            startAudio();
        }

        public function update():void {
            if (!initialized) {
                if (stage) {
                    initialize();
                }
                return;
            }

            var dt:Number = 1.0 / FRAME_RATE;
            currentFrame++;
            songTime += dt;

            while (songTime >= nextBeatTime) {
                onBeat();
                nextBeatTime += beatDuration;
            }

            updatePoseIntent();
            playerPoseAngle = normalizeAngle(playerPoseAngle + shortestAngle(playerPoseAngle, targetPoseAngle) * 0.18);
            poseSpin += 0.04 + combo * 0.0008;

            spectralPulse *= 0.94;
            sparkleFlash *= 0.90;
            bassEnergy *= 0.93;
            snareSplash *= 0.88;
            hatEnergy *= 0.72;
            tailNoise *= 0.97;
            runwayPulse *= 0.90;
            finisherBloom *= 0.92;
            dressCharge = Math.max(0.0, dressCharge - 0.005);
            outfitTier = Math.min(4, int(dressCharge / 20.0));

            updateCues(dt);
            updateEnemy(dt);
            updateParticles(dt);

            renderFrameBuffer();
            renderRunway();
            renderEnemy();
            renderPlayer();
            renderParticles();
            updateHud();
        }

        private function buildHud():void {
            titleField = makeField(24, 0xF5F8FF, TextFormatAlign.LEFT, true, 18, 14, 500, 30);
            scoreField = makeField(16, 0xD7F0FF, TextFormatAlign.LEFT, false, 18, 48, 360, 24);
            comboField = makeField(16, 0xFFE4BE, TextFormatAlign.LEFT, false, 18, 72, 560, 24);
            wardrobeField = makeField(15, 0xBEE6FF, TextFormatAlign.LEFT, false, 18, 96, 620, 24);
            enemyField = makeField(15, 0xFFD7B8, TextFormatAlign.LEFT, false, 18, 120, 620, 24);
            lockField = makeField(18, 0xFFF6CC, TextFormatAlign.RIGHT, true, 510, 18, 432, 28);
            helpField = makeField(14, 0xE7EEF9, TextFormatAlign.LEFT, false, 18, 482, 924, 22);
            systemField = makeField(13, 0xB8C7D9, TextFormatAlign.LEFT, false, 18, 506, 924, 18);
        }

        private function makeField(size:int, color:uint, align:String, bold:Boolean, xPos:Number, yPos:Number, widthValue:Number, heightValue:Number):TextField {
            var field:TextField = new TextField();
            var format:TextFormat = new TextFormat("Verdana", size, color, bold, null, null, null, null, align);
            field.defaultTextFormat = format;
            field.autoSize = TextFieldAutoSize.LEFT;
            field.multiline = false;
            field.wordWrap = false;
            field.selectable = false;
            field.mouseEnabled = false;
            field.x = xPos;
            field.y = yPos;
            field.width = widthValue;
            field.height = heightValue;
            addChild(field);
            return field;
        }

        private function startAudio():void {
            sound = new Sound();
            sound.addEventListener(SampleDataEvent.SAMPLE_DATA, onSoundData);
            channel = sound.play();
            if (channel) {
                channel.soundTransform = new SoundTransform(0.72);
            }
        }

        private function onSoundData(event:SampleDataEvent):void {
            const sampleRate:Number = 44100.0;
            const sampleCount:int = 2048;
            const tau:Number = Math.PI * 2.0;

            for (var sampleIndex:int = 0; sampleIndex < sampleCount; sampleIndex++) {
                var t:Number = audioCursor / sampleRate;
                var beat:Number = t * bpm / 60.0;
                var beatPosition:Number = beat % 4.0;
                var kickEnv:Number = envelopeFromTrigger(beatPosition, 0.0, 0.28) + 0.65 * envelopeFromTrigger(beatPosition, 2.0, 0.22);
                var snareEnv:Number = 0.9 * envelopeFromTrigger(beatPosition, 1.0, 0.12) + envelopeFromTrigger(beatPosition, 3.0, 0.12);
                var hatEnv:Number = gridEnvelope(beat * 4.0, 0.08);
                var wobble:Number = 0.5 + 0.5 * Math.sin(t * tau * (0.75 + matterDisruption * 0.5));
                var bassFreq:Number = 42.0 + 24.0 * wobble + combo * 0.12;

                sparkleAudio *= 0.9992;
                tailNoise *= 0.9994;

                var kick:Number = Math.sin(t * tau * (44.0 + 32.0 * kickEnv)) * kickEnv * 0.56;
                var bass:Number = Math.sin(t * tau * bassFreq + 0.42 * Math.sin(t * tau * bassFreq * 0.5)) * 0.28;
                var snare:Number = randomNoise(int(audioCursor + sampleIndex * 19.0)) * snareEnv * 0.26;
                var hat:Number = randomNoise(int(audioCursor * 1.7 + sampleIndex * 47.0)) * hatEnv * 0.09;
                var sparkle:Number = Math.sin(t * tau * (660.0 + 150.0 * Math.sin(t * 5.0))) * sparkleAudio * 0.13;
                var disruption:Number = randomNoise(int(audioCursor * 0.6 + sampleIndex * 97.0)) * tailNoise * 0.07;

                var left:Number = clampAudio(kick + bass + snare + hat + sparkle + disruption);
                var right:Number = clampAudio(kick + bass * 0.93 - snare * 0.06 + hat * 0.84 + sparkle * 1.04 - disruption * 0.72);
                event.data.writeFloat(left);
                event.data.writeFloat(right);
                audioCursor++;
            }
        }

        private function onBeat():void {
            beatIndex++;
            bassEnergy = 1.0;
            hatEnergy = 1.0;
            spectralPulse = Math.min(1.0, spectralPulse + 0.18);
            runwayPulse = 1.0;
            if (beatIndex % 2 == 0) {
                snareSplash = 1.0;
            }

            if (currentEnemy) {
                currentEnemy.spawnHint = Math.min(1.0, currentEnemy.spawnHint + 0.08);
                currentEnemy.tailWave = pseudo(beatIndex * 0.77 + encounterIndex * 1.31);
                if (beatIndex % 2 == 0) {
                    currentEnemy.telegraphLane = int(pseudo(beatIndex * 0.43 + encounterIndex * 2.71 + currentEnemy.archetype * 0.7) * LANE_COUNT);
                }
            }

            if (lockReady) {
                if (!(tutorialActive && tutorialStep >= 6)) {
                    lockTargetAngle = normalizeAngle(lockTargetAngle + 0.45 + pseudo(beatIndex * 0.61 + encounterIndex * 4.0) * 0.95);
                }
                finisherBloom = Math.min(1.0, finisherBloom + 0.10);
                lastCueHint = "Pose lock window is live. Hold a silhouette and press SPACE.";
                return;
            }

            if (tutorialActive) {
                updateTutorialBeat();
                return;
            }

            spawnCue(0);
            if (beatIndex % 4 == 0 && combo >= 8) {
                spawnCue(1);
            }
        }

        private function spawnCue(offset:int):void {
            var cue:DanceCue = new DanceCue();
            var laneChoice:int = int(pseudo(beatIndex * 2.713 + encounterIndex * 5.117 + offset * 11.1) * LANE_COUNT);
            var telegraphLane:int = currentEnemy ? currentEnemy.telegraphLane : laneChoice;
            if (currentEnemy && (beatIndex % 3 == 0 || offset > 0)) {
                laneChoice = (telegraphLane + offset) % LANE_COUNT;
            }
            cue.lane = laneChoice;
            cue.y = -36.0 - offset * 72.0;
            cue.speed = 232.0 + encounterIndex * 11.0 + pseudo(beatIndex * 1.39 + offset) * 62.0;
            cue.color = laneColor(cue.lane);
            cue.size = 16.0 + pseudo(beatIndex * 2.47 + offset) * 10.0;
            cue.wobble = pseudo(beatIndex * 3.31 + offset) * Math.PI * 2.0;
            cue.anticipation = 0.35 + pseudo(beatIndex * 4.11 + offset) * 0.5;
            cue.form = (cue.lane + (currentEnemy ? currentEnemy.archetype : 0) + offset) % 4;
            cue.spin = pseudo(beatIndex * 3.89 + offset * 4.0) * 2.0 - 1.0;
            cue.trail = 20.0 + pseudo(beatIndex * 4.91 + offset * 1.8) * 26.0;
            cues.push(cue);
            lastCueHint = laneNames[cue.lane] + " lane is hot. " + laneGlyphs[cue.lane] + " pattern incoming.";
        }

        private function updatePoseIntent():void {
            var sumX:Number = 0.0;
            var sumY:Number = 0.0;
            var activeCount:int = 0;

            for (var lane:int = 0; lane < LANE_COUNT; lane++) {
                if (laneHeld(lane)) {
                    var laneAngle:Number = poseAngleForLane(lane);
                    sumX += Math.cos(laneAngle);
                    sumY += Math.sin(laneAngle);
                    activeCount++;
                }
            }

            if (activeCount > 0) {
                targetPoseAngle = Math.atan2(sumY, sumX);
            }
        }

        private function laneHeld(lane:int):Boolean {
            switch (lane) {
                case 0:
                    return keyDown[Keyboard.A] || keyDown[Keyboard.LEFT];
                case 1:
                    return keyDown[Keyboard.S] || keyDown[Keyboard.DOWN];
                case 2:
                    return keyDown[Keyboard.K] || keyDown[Keyboard.UP];
                case 3:
                    return keyDown[Keyboard.L] || keyDown[Keyboard.RIGHT];
            }
            return false;
        }

        private function onKeyDown(event:KeyboardEvent):void {
            if (keyDown[event.keyCode]) {
                return;
            }
            keyDown[event.keyCode] = true;

            var lane:int = laneFromKey(event.keyCode);
            if (lane >= 0) {
                if (tutorialActive && tutorialStep < 4) {
                    handleTutorialLanePrimer(lane);
                    return;
                }
                pressLane(lane);
            } else if (event.keyCode == Keyboard.SPACE) {
                if (tutorialActive && tutorialStep < 6) {
                    lastCueHint = "Tutorial: finish lane primers and cue hits before using SPACE.";
                    return;
                }
                attemptPoseLock();
            }
        }

        private function onKeyUp(event:KeyboardEvent):void {
            delete keyDown[event.keyCode];
        }

        private function laneFromKey(keyCode:uint):int {
            switch (keyCode) {
                case Keyboard.A:
                case Keyboard.LEFT:
                    return 0;
                case Keyboard.S:
                case Keyboard.DOWN:
                    return 1;
                case Keyboard.K:
                case Keyboard.UP:
                    return 2;
                case Keyboard.L:
                case Keyboard.RIGHT:
                    return 3;
            }
            return -1;
        }

        private function pressLane(lane:int):void {
            var bestCue:DanceCue = null;
            var bestDistance:Number = 99999.0;
            var hitWindow:Number = tutorialActive ? HIT_WINDOW * 1.35 : HIT_WINDOW;
            var cueIndex:int;
            var cue:DanceCue;

            targetPoseAngle = poseAngleForLane(lane);

            for (cueIndex = 0; cueIndex < cues.length; cueIndex++) {
                cue = cues[cueIndex] as DanceCue;
                if (cue.lane != lane) {
                    continue;
                }
                var distance:Number = Math.abs(cue.y - STRIKE_Y);
                if (distance < bestDistance) {
                    bestDistance = distance;
                    bestCue = cue;
                }
            }

            if (bestCue && bestDistance <= hitWindow) {
                cues.splice(cues.indexOf(bestCue), 1);
                scoreCue(bestCue, 1.0 - bestDistance / hitWindow);
                return;
            }

            registerMistake("Sparkle drifted off-beat. The LiteMite glue-stall field thickens.");
        }

        private function scoreCue(cue:DanceCue, accuracy:Number):void {
            var xPos:Number = Number(laneCenters[cue.lane]);
            score += 150 + int(accuracy * 240.0) + combo * 12;
            combo++;
            dressCharge = Math.min(100.0, dressCharge + 11.0 + accuracy * 9.0);
            outfitTier = Math.min(4, int(dressCharge / 20.0));
            matterDisruption = Math.max(0.05, matterDisruption - 0.05 - accuracy * 0.02);
            emberence = Math.min(1.0, emberence + 0.06);
            spectralPulse = Math.min(1.0, spectralPulse + 0.24);
            sparkleFlash = Math.min(1.0, sparkleFlash + 0.38);
            sparkleAudio = Math.min(2.0, sparkleAudio + 0.34 + accuracy * 0.46);
            tailNoise = Math.max(0.0, tailNoise - 0.12);
            runwayPulse = Math.min(1.0, runwayPulse + 0.42);
            lastCueHint = "Sparkle danced into fresh clothing and shaved the light-tail.";

            if (currentEnemy) {
                currentEnemy.integrity -= 0.12 + accuracy * 0.15;
                currentEnemy.spawnHint = Math.min(1.0, currentEnemy.spawnHint + 0.18);
                currentEnemy.tailBacklash *= 0.45;
                if (currentEnemy.integrity <= 0.36 && !lockReady) {
                    startPoseLock();
                }
            }

            emitBurst(xPos, STRIKE_Y, cue.color, 10 + int(accuracy * 8.0), true);

            if (tutorialActive) {
                onTutorialCueScored();
            }
        }

        private function registerMistake(note:String):void {
            if (tutorialActive) {
                combo = Math.max(0, combo - 1);
                matterDisruption = Math.min(1.0, matterDisruption + 0.05);
                emberence = Math.min(1.0, emberence + 0.04);
                sparkleFlash = Math.min(1.0, sparkleFlash + 0.08);
                tailNoise = Math.min(1.2, tailNoise + 0.10);
                lastCueHint = "Tutorial assist: " + note;

                if (currentEnemy) {
                    currentEnemy.tailBacklash = Math.min(1.0, currentEnemy.tailBacklash + 0.10);
                    currentEnemy.integrity = Math.min(1.0, currentEnemy.integrity + 0.02);
                    currentEnemy.spawnHint = Math.min(1.0, currentEnemy.spawnHint + 0.04);
                }
                return;
            }

            combo = 0;
            matterDisruption = Math.min(1.0, matterDisruption + 0.14);
            emberence = Math.min(1.0, emberence + 0.12);
            sparkleFlash = Math.min(1.0, sparkleFlash + 0.14);
            tailNoise = Math.min(1.2, tailNoise + 0.28);
            lastCueHint = note;

            if (currentEnemy) {
                currentEnemy.tailBacklash = Math.min(1.0, currentEnemy.tailBacklash + 0.32);
                currentEnemy.integrity = Math.min(1.0, currentEnemy.integrity + 0.06);
                currentEnemy.spawnHint = Math.min(1.0, currentEnemy.spawnHint + 0.12);
            }
        }

        private function startPoseLock():void {
            lockReady = true;
            lockTimer = beatDuration * 2.5;
            lockTargetAngle = normalizeAngle(pseudo(encounterIndex * 4.13 + beatIndex * 0.7) * Math.PI * 2.0);
            finisherBloom = Math.min(1.0, finisherBloom + 0.24);
            lastCueHint = "Pose lock is armed. Hold a silhouette and hit SPACE to fold the syncrosequence tail.";
        }

        private function attemptPoseLock():void {
            if (!currentEnemy) {
                return;
            }
            if (!lockReady) {
                registerMistake("The pose lock cracked early. Thin the tail first.");
                return;
            }

            var angleError:Number = Math.abs(shortestAngle(playerPoseAngle, lockTargetAngle));
            var timing:Number = lockTimer / (beatDuration * 2.5);
            var quality:Number = (1.0 - Math.min(1.0, angleError / 0.90)) * 0.7 + timing * 0.3;

            if (quality >= 0.72) {
                finishPoseLock(quality);
            } else {
                failPoseLock(quality);
            }
        }

        private function finishPoseLock(quality:Number):void {
            score += 1200 + int(quality * 900.0) + combo * 24;
            combo += 3;
            dressCharge = Math.min(100.0, dressCharge + 24.0);
            outfitTier = Math.min(4, int(dressCharge / 20.0));
            sparkleFlash = 1.0;
            spectralPulse = 1.0;
            finisherBloom = 1.0;
            sparkleAudio = Math.min(3.0, sparkleAudio + 1.4);
            matterDisruption = Math.max(0.04, matterDisruption - 0.16);
            tailNoise = 0.0;
            lockReady = false;
            lockTimer = 0.0;
            lastCueHint = "Pose locked. The LiteMite tail collapsed into white noise.";

            if (currentEnemy) {
                currentEnemy.defeated = true;
                currentEnemy.explosion = 1.0 + quality * 0.6;
                currentEnemy.tailBacklash = 0.0;
                emitBurst(currentEnemy.x, currentEnemy.y, 0xFFF0C0, 32, true);
            }

            if (tutorialActive && tutorialStep >= 6) {
                tutorialStep = 7;
                tutorialActive = false;
                lastCueHint = "Tutorial complete. Freestyle the seams and crush the swarm.";
            }
        }

        private function failPoseLock(quality:Number):void {
            lockReady = false;
            lockTimer = 0.0;

            if (tutorialActive) {
                combo = Math.max(0, combo - 2);
                matterDisruption = Math.min(1.0, matterDisruption + 0.08);
                tailNoise = Math.min(1.2, tailNoise + 0.24);
                sparkleFlash = Math.min(1.0, sparkleFlash + 0.10);
                finisherBloom = Math.min(1.0, finisherBloom + 0.16);
                lastCueHint = "Tutorial: adjust pose and press SPACE again.";
                if (currentEnemy) {
                    currentEnemy.tailBacklash = Math.min(1.0, currentEnemy.tailBacklash + 0.24);
                    currentEnemy.integrity = Math.min(1.0, currentEnemy.integrity + 0.06 + (1.0 - quality) * 0.04);
                }
                return;
            }

            combo = 0;
            matterDisruption = Math.min(1.0, matterDisruption + 0.22);
            tailNoise = Math.min(1.2, tailNoise + 0.76);
            sparkleFlash = Math.min(1.0, sparkleFlash + 0.24);
            finisherBloom = Math.min(1.0, finisherBloom + 0.34);
            lastCueHint = "Poor lock. The light-tail falls backward through the glue-stall field.";

            if (currentEnemy) {
                currentEnemy.tailBacklash = 1.0;
                currentEnemy.integrity = Math.min(1.0, currentEnemy.integrity + 0.18 + (1.0 - quality) * 0.08);
                emitBurst(currentEnemy.x - 80.0, currentEnemy.y + 38.0, 0xFF7C58, 16, false);
            }
        }

        private function updateCues(dt:Number):void {
            var missWindow:Number = tutorialActive ? MISS_WINDOW * 1.5 : MISS_WINDOW;
            for (var cueIndex:int = cues.length - 1; cueIndex >= 0; cueIndex--) {
                var cue:DanceCue = cues[cueIndex] as DanceCue;
                cue.y += cue.speed * dt;
                cue.wobble += dt * 4.6;

                if (cue.y > STRIKE_Y + missWindow) {
                    cues.splice(cueIndex, 1);
                    registerMistake("A sync seam slipped by. Denser emberence warns of another LiteMite swell.");
                    emitBurst(Number(laneCenters[cue.lane]), STRIKE_Y, 0xFF8C58, 8, false);
                }
            }
        }

        private function updateEnemy(dt:Number):void {
            if (!currentEnemy) {
                spawnEncounter();
                return;
            }

            currentEnemy.phase += dt * currentEnemy.orbitSpeed;

            if (currentEnemy.defeated) {
                currentEnemy.explosion -= dt * 0.95;
                currentEnemy.spawnHint = currentEnemy.explosion;
                if (currentEnemy.explosion <= 0.0) {
                    spawnEncounter();
                }
                return;
            }

            currentEnemy.x = 716.0 + Math.sin(songTime * 1.7 + currentEnemy.signature * Math.PI * 2.0) * (24.0 + currentEnemy.spawnHint * 22.0);
            currentEnemy.y = 156.0 + currentEnemy.signature * 128.0 + Math.sin(songTime * 2.5 + currentEnemy.phase) * (9.0 + currentEnemy.spawnHint * 6.0);
            currentEnemy.spawnHint += (0.30 + matterDisruption * 0.42 - currentEnemy.spawnHint) * 0.04;
            currentEnemy.tailBacklash *= 0.93;
            currentEnemy.tailWave = 0.45 + 0.35 * Math.sin(songTime * 3.4 + currentEnemy.phase * 1.2);

            if (lockReady) {
                lockTimer -= dt;
                if (lockTimer <= 0.0) {
                    failPoseLock(0.0);
                }
            }
        }

        private function updateParticles(dt:Number):void {
            for (var particleIndex:int = particles.length - 1; particleIndex >= 0; particleIndex--) {
                var particle:SparkleParticle = particles[particleIndex] as SparkleParticle;
                particle.life -= dt;
                if (particle.life <= 0.0) {
                    particles.splice(particleIndex, 1);
                    continue;
                }
                particle.x += particle.vx * dt;
                particle.y += particle.vy * dt;
                particle.vx *= 0.99;
                particle.vy *= 0.99;
                particle.vy += 12.0 * dt;
            }
        }

        private function spawnEncounter():void {
            var archetype:int;
            cues = [];
            encounterIndex++;
            currentEnemy = new LiteMiteState();
            archetype = encounterIndex % encounterArchetypes.length;
            currentEnemy.archetype = archetype;
            currentEnemy.name = encounterArchetypes[archetype] + " " + encounterIndex;
            currentEnemy.x = 718.0;
            currentEnemy.signature = pseudo(encounterIndex * 1.73);
            currentEnemy.y = 156.0 + currentEnemy.signature * 128.0;
            currentEnemy.integrity = 1.0;
            currentEnemy.spawnHint = 0.48;
            currentEnemy.tailBacklash = 0.0;
            currentEnemy.tailWave = 0.4;
            currentEnemy.swarmCount = int(Math.min(18, 6 + encounterIndex + archetype));
            currentEnemy.phase = pseudo(encounterIndex * 2.91) * Math.PI * 2.0;
            currentEnemy.defeated = false;
            currentEnemy.explosion = 0.0;
            currentEnemy.coreColor = archetypeCoreColor(archetype);
            currentEnemy.accentColor = archetypeAccentColor(archetype);
            currentEnemy.telegraphLane = (archetype + encounterIndex) % LANE_COUNT;
            currentEnemy.orbitSpeed = 1.3 + archetype * 0.24;
            currentEnemy.tailSegments = 7 + archetype;

            lockReady = false;
            lockTimer = 0.0;
            if (!tutorialActive) {
                lastCueHint = "A " + encounterArchetypes[archetype] + " condenses in the visible spectrum. Watch the telegraphed lane.";
            }
        }

        private function emitBurst(xPos:Number, yPos:Number, color:uint, count:int, upward:Boolean):void {
            for (var index:int = 0; index < count; index++) {
                var particle:SparkleParticle = new SparkleParticle();
                var angle:Number = pseudo(index * 19.0 + currentFrame * 0.31) * Math.PI * 2.0;
                var speed:Number = 30.0 + pseudo(index * 7.0 + currentFrame * 0.13) * 140.0;
                particle.x = xPos;
                particle.y = yPos;
                particle.vx = Math.cos(angle) * speed;
                particle.vy = Math.sin(angle) * speed - (upward ? 42.0 : 0.0);
                particle.life = 0.35 + pseudo(index * 11.0 + currentFrame * 0.09) * 0.55;
                particle.size = 3.0 + pseudo(index * 13.0 + currentFrame * 0.17) * 6.0;
                particle.color = color;
                particles.push(particle);
            }
        }

        private function renderFrameBuffer():void {
            var enemyNx:Number = currentEnemy ? currentEnemy.x / VIEW_W : 0.75;
            var enemyNy:Number = currentEnemy ? currentEnemy.y / VIEW_H : 0.36;
            var dressGlow:Number = dressCharge / 100.0;
            var comboGlow:Number = Math.min(combo / 18.0, 1.0);
            var printGrainStrength:Number = tutorialActive ? 6.0 : 10.0;
            var printBanding:Number = tutorialActive ? 12.0 : 16.0;
            var enemyColor:uint = currentEnemy ? currentEnemy.coreColor : 0xFFECA4;
            var accentColor:uint = currentEnemy ? currentEnemy.accentColor : 0x84E4FF;
            var enemyRed:Number = ((enemyColor >> 16) & 0xFF) / 255.0;
            var enemyGreen:Number = ((enemyColor >> 8) & 0xFF) / 255.0;
            var accentBlue:Number = (accentColor & 0xFF) / 255.0;

            backgroundData.lock();
            for (var py:int = 0; py < BG_H; py++) {
                var ny:Number = py / Number(BG_H);
                for (var px:int = 0; px < BG_W; px++) {
                    var nx:Number = px / Number(BG_W);
                    var sweepA:Number = 0.5 + 0.5 * Math.sin(nx * 14.0 + songTime * 2.8 + ny * 4.0);
                    var sweepB:Number = 0.5 + 0.5 * Math.sin(ny * 20.0 - songTime * 4.2 + nx * 3.2);
                    var visibleShift:Number = 0.5 + 0.5 * Math.sin((nx + ny) * 18.0 - songTime * 6.0 + poseSpin);
                    var disruption:Number = matterDisruption * (0.45 + 0.55 * Math.sin(songTime * 7.2 + nx * 9.0));
                    var laneGlow:Number = 0.0;
                    var emberPocket:Number = 0.0;
                    var telegraphGlow:Number = 0.0;
                    var laneIndex:int;

                    for (laneIndex = 0; laneIndex < LANE_COUNT; laneIndex++) {
                        var laneNx:Number = Number(laneCenters[laneIndex]) / VIEW_W;
                        laneGlow += Math.max(0.0, 1.0 - Math.abs(nx - laneNx) * 18.0) * 0.08;
                        if (currentEnemy && laneIndex == currentEnemy.telegraphLane) {
                            telegraphGlow += Math.max(0.0, 1.0 - Math.abs(nx - laneNx) * 20.0) * 0.22;
                        }
                    }

                    if (currentEnemy) {
                        var dx:Number = nx - enemyNx;
                        var dy:Number = ny - enemyNy;
                        var dist:Number = Math.sqrt(dx * dx + dy * dy);
                        emberPocket += Math.max(0.0, 1.0 - dist * 5.0) * (0.2 + currentEnemy.spawnHint * 0.8);

                        for (var tailIndex:int = 0; tailIndex < 3; tailIndex++) {
                            var tailNx:Number = enemyNx - 0.06 * tailIndex;
                            var tailNy:Number = enemyNy + (currentEnemy.tailBacklash > 0.2 ? 0.03 * tailIndex * tailIndex : Math.sin(songTime * 3.0 + tailIndex) * 0.015);
                            dx = nx - tailNx;
                            dy = ny - tailNy;
                            dist = Math.sqrt(dx * dx + dy * dy);
                            emberPocket += Math.max(0.0, 1.0 - dist * (12.0 + tailIndex * 2.0)) * 0.18;
                        }
                    }

                    var red:int = clampByte(12.0 + 72.0 * sweepA + 128.0 * emberPocket * enemyRed + 58.0 * spectralPulse + 56.0 * disruption + 44.0 * runwayPulse + 36.0 * finisherBloom);
                    var green:int = clampByte(10.0 + 52.0 * sweepB + 82.0 * laneGlow + 84.0 * comboGlow + 52.0 * visibleShift + 88.0 * emberPocket * enemyGreen + 54.0 * telegraphGlow);
                    var blue:int = clampByte(24.0 + 88.0 * (1.0 - sweepA) + 112.0 * dressGlow + 50.0 * sweepB + 72.0 * sparkleFlash + 64.0 * telegraphGlow + 62.0 * finisherBloom * accentBlue);

                    var grainSeed:Number = px * 0.73 + py * 1.17 + currentFrame * 0.21;
                    var grain:Number = (pseudo(grainSeed) * 2.0 - 1.0) * printGrainStrength;
                    var paper:Number = (Math.sin((px + py * 0.7) * 0.095 + songTime * 1.4) * 0.5 + 0.5) * (printGrainStrength * 0.35);

                    red = posterizeChannel(clampByte(red + grain + paper * 0.6), printBanding);
                    green = posterizeChannel(clampByte(green + grain * 0.85 + paper * 0.4), printBanding);
                    blue = posterizeChannel(clampByte(blue + grain * 1.05 + paper * 0.25), printBanding);

                    backgroundData.setPixel(px, py, (red << 16) | (green << 8) | blue);
                }
            }
            backgroundData.unlock();
        }

        private function renderRunway():void {
            var g:Graphics = runwayLayer.graphics;
            var arenaTopY:Number = 82.0;
            var arenaBottomY:Number = 466.0;
            var arenaTopLeft:Number = 330.0;
            var arenaTopRight:Number = 630.0;
            var arenaBottomLeft:Number = 284.0;
            var arenaBottomRight:Number = 706.0;
            var ink:uint = 0x111111;
            g.clear();

            g.lineStyle(6, ink, 0.9, true);
            g.beginFill(0x0F1A25, 0.36 + runwayPulse * 0.08);
            g.moveTo(arenaTopLeft, arenaTopY);
            g.lineTo(arenaTopRight, arenaTopY);
            g.lineTo(arenaBottomRight, arenaBottomY);
            g.lineTo(arenaBottomLeft, arenaBottomY);
            g.lineTo(arenaTopLeft, arenaTopY);
            g.endFill();

            g.lineStyle(3, 0x6CD6FF, 0.30 + runwayPulse * 0.22, true);
            g.moveTo(arenaTopLeft + 4.0, arenaTopY + 4.0);
            g.lineTo(arenaTopRight - 4.0, arenaTopY + 4.0);
            g.lineTo(arenaBottomRight - 6.0, arenaBottomY - 6.0);
            g.lineTo(arenaBottomLeft + 6.0, arenaBottomY - 6.0);
            g.lineTo(arenaTopLeft + 4.0, arenaTopY + 4.0);

            for (var stripe:int = 0; stripe < 10; stripe++) {
                var stripeT:Number = stripe / 9.0;
                var stripeY:Number = arenaTopY + (STRIKE_Y - arenaTopY) * stripeT;
                var stripeLeft:Number = arenaTopLeft + (arenaBottomLeft - arenaTopLeft) * stripeT;
                var stripeRight:Number = arenaTopRight + (arenaBottomRight - arenaTopRight) * stripeT;
                g.lineStyle(1, 0x27354F, 0.22 + 0.16 * Math.sin(songTime * 4.0 + stripe));
                g.moveTo(stripeLeft, stripeY);
                g.lineTo(stripeRight, stripeY);
            }

            for (var lane:int = 0; lane < LANE_COUNT; lane++) {
                var laneX:Number = Number(laneCenters[lane]);
                var laneTopX:Number = VIEW_W * 0.5 + (laneX - VIEW_W * 0.5) * 0.24;
                var laneColorValue:uint = laneColor(lane);
                var laneAlpha:Number = laneHeld(lane) ? 0.22 + spectralPulse * 0.10 : 0.06 + spectralPulse * 0.08;
                g.lineStyle(5.0 + lane * 0.4, ink, 0.86, true);
                g.moveTo(laneTopX, arenaTopY + 10.0);
                g.lineTo(laneX, STRIKE_Y + 12.0);
                g.lineStyle(3, laneColorValue, 0.28 + laneAlpha + runwayPulse * 0.20, true);
                g.moveTo(laneTopX, arenaTopY + 10.0);
                g.lineTo(laneX, STRIKE_Y + 12.0);
                g.lineStyle(2, laneColorValue, 0.42 + laneAlpha);
                g.moveTo(laneTopX - 16.0, arenaTopY + 18.0);
                g.lineTo(laneX - 24.0, STRIKE_Y);
                g.moveTo(laneTopX + 16.0, arenaTopY + 18.0);
                g.lineTo(laneX + 24.0, STRIKE_Y);
                drawLaneSigil(g, laneTopX, arenaTopY + 30.0, lane, 10.0 + spectralPulse * 4.0, 0.35 + laneAlpha);
                drawLaneSigil(g, laneX, STRIKE_Y + 24.0, lane, 14.0 + (laneHeld(lane) ? 4.0 : 0.0), 0.55 + laneAlpha);
            }

            if (currentEnemy && !currentEnemy.defeated) {
                var telegraphX:Number = Number(laneCenters[currentEnemy.telegraphLane]);
                g.lineStyle(2, currentEnemy.accentColor, 0.42 + currentEnemy.spawnHint * 0.32);
                g.beginFill(currentEnemy.accentColor, 0.08 + currentEnemy.spawnHint * 0.08);
                g.moveTo(currentEnemy.x, currentEnemy.y + 12.0);
                g.lineTo(telegraphX - 34.0, STRIKE_Y);
                g.lineTo(telegraphX + 34.0, STRIKE_Y);
                g.lineTo(currentEnemy.x, currentEnemy.y + 12.0);
                g.endFill();
                drawLaneSigil(g, telegraphX, STRIKE_Y - 32.0, currentEnemy.telegraphLane, 16.0 + currentEnemy.spawnHint * 8.0, 0.7 + currentEnemy.spawnHint * 0.2);
            }

            g.lineStyle(5, 0xFFF0B8, 0.86);
            g.moveTo(352.0, STRIKE_Y);
            g.lineTo(688.0, STRIKE_Y);
            g.lineStyle(1, 0xFFB768, 0.70);
            g.moveTo(352.0, STRIKE_Y + 8.0 * Math.sin(songTime * 4.0));
            g.lineTo(688.0, STRIKE_Y + 8.0 * Math.sin(songTime * 4.0));

            for each (var cue:DanceCue in cues) {
                laneX = Number(laneCenters[cue.lane]);
                var size:Number = cue.size * (0.84 + 0.22 * Math.sin(songTime * 10.0 + cue.wobble));
                var cueX:Number = laneX + Math.sin(songTime * 8.0 + cue.wobble) * cue.spin * 6.0;
                g.lineStyle(2.0 + size * 0.08, ink, 0.92, true);
                g.beginFill(cue.color, 0.95);
                drawCueShape(g, cue, cueX, cue.y, size);
                g.endFill();
                g.lineStyle(0, 0, 0);
                g.beginFill(lightenColor(cue.color, 0.32), 0.45);
                drawCueShape(g, cue, cueX - size * 0.16, cue.y - size * 0.18, size * 0.62);
                g.endFill();
                g.lineStyle(2, cue.color, 0.42);
                g.moveTo(cueX, cue.y - size * 1.2);
                g.curveTo(cueX + cue.spin * cue.trail * 0.34, cue.y - cue.trail, cueX, cue.y - cue.trail * 1.55 - cue.anticipation * 18.0);
            }
        }

        private function renderEnemy():void {
            var g:Graphics = enemyLayer.graphics;
            g.clear();

            if (!currentEnemy) {
                return;
            }

            var centerX:Number = currentEnemy.x;
            var centerY:Number = currentEnemy.y;
            var tailDrop:Number = currentEnemy.tailBacklash * 22.0;
            var baseColor:uint = currentEnemy.defeated ? 0xFFF0D0 : currentEnemy.coreColor;
            var accentColor:uint = currentEnemy.accentColor;
            var tailCount:int = currentEnemy.tailSegments;
            var telegraphX:Number = Number(laneCenters[currentEnemy.telegraphLane]);
            var ink:uint = 0x101010;
            var baseShade:uint = darkenColor(baseColor, 0.28);
            var baseHigh:uint = lightenColor(baseColor, 0.20);

            g.lineStyle(0, 0, 0);
            g.beginFill(0x000000, 0.26);
            g.drawEllipse(centerX - 54.0, centerY + 30.0, 108.0, 24.0);
            g.endFill();

            g.lineStyle(3.0 + currentEnemy.spawnHint * 2.0, ink, 0.90, true);
            for (var tailSegment:int = 0; tailSegment < tailCount; tailSegment++) {
                var startX:Number = centerX - tailSegment * 28.0;
                var startY:Number = centerY + Math.sin(songTime * 4.0 + tailSegment * 0.8 + currentEnemy.phase) * (8.0 + tailSegment) + tailDrop * tailSegment * 0.32;
                var endX:Number = centerX - (tailSegment + 1) * 28.0;
                var endY:Number = centerY + Math.sin(songTime * 4.0 + (tailSegment + 1) * 0.8 + currentEnemy.phase) * (8.0 + tailSegment + 1.0) + tailDrop * (tailSegment + 1) * 0.32;
                var controlX:Number = centerX - (tailSegment + 0.5) * 28.0 + Math.sin(songTime * 3.6 + currentEnemy.phase + tailSegment) * 18.0 * currentEnemy.tailWave;
                var controlY:Number = (startY + endY) * 0.5 + Math.cos(songTime * 2.8 + tailSegment * 0.7) * 8.0;
                g.moveTo(startX, startY);
                g.curveTo(controlX, controlY, endX, endY);
            }

            g.lineStyle(4, ink, 0.82, true);
            g.moveTo(centerX, centerY);
            g.lineTo(telegraphX, STRIKE_Y - 20.0);

            g.lineStyle(2, accentColor, 0.46 + currentEnemy.spawnHint * 0.28, true);
            g.moveTo(centerX, centerY);
            g.lineTo(telegraphX, STRIKE_Y - 20.0);

            for (var mote:int = 0; mote < currentEnemy.swarmCount; mote++) {
                var angle:Number = currentEnemy.phase * 2.2 + mote * (Math.PI * 2.0 / currentEnemy.swarmCount);
                var radius:Number = 20.0 + 10.0 * Math.sin(songTime * 3.2 + mote + encounterIndex * 0.2);
                var moteX:Number = centerX + Math.cos(angle) * radius;
                var moteY:Number = centerY + Math.sin(angle) * radius * 0.58;
                g.beginFill(accentColor, 0.24 + currentEnemy.spawnHint * 0.32);
                g.drawCircle(moteX, moteY, 4.0 + 2.0 * Math.sin(songTime * 6.0 + mote));
                g.endFill();
            }

            switch (currentEnemy.archetype) {
                case 0:
                    g.lineStyle(4.5, ink, 0.95, true);
                    g.beginFill(baseShade, 0.88);
                    drawBurst(g, centerX, centerY, 34.0 + currentEnemy.spawnHint * 12.0, 16.0 + currentEnemy.spawnHint * 6.0, 6, currentEnemy.phase * 0.7);
                    g.endFill();
                    g.lineStyle(0, 0, 0);
                    g.beginFill(baseHigh, 0.46);
                    g.drawCircle(centerX - 6.0, centerY - 8.0, 9.0 + currentEnemy.spawnHint * 2.0);
                    g.endFill();
                    break;
                case 1:
                    g.lineStyle(3.5, ink, 0.95, true);
                    g.beginFill(baseShade, 0.72);
                    g.drawCircle(centerX - 16.0, centerY - 3.0, 18.0 + currentEnemy.spawnHint * 6.0);
                    g.drawCircle(centerX + 10.0, centerY + 7.0, 14.0 + currentEnemy.spawnHint * 5.0);
                    g.drawCircle(centerX + 28.0, centerY - 18.0, 8.0 + currentEnemy.spawnHint * 4.0);
                    g.endFill();
                    drawRibbon(g, centerX - 28.0, centerY + 4.0, centerX + 30.0, centerY + 9.0, 0.85, accentColor, 0.64, 5.0);
                    drawRibbon(g, centerX - 24.0, centerY - 12.0, centerX + 24.0, centerY - 6.0, -0.72, accentColor, 0.42, 3.0);
                    break;
                case 2:
                    for (var orbit:int = 0; orbit < 3; orbit++) {
                        var petalAngle:Number = currentEnemy.phase * 1.8 + orbit * Math.PI * 2.0 / 3.0;
                        var petalX:Number = centerX + Math.cos(petalAngle) * (20.0 + currentEnemy.spawnHint * 8.0);
                        var petalY:Number = centerY + Math.sin(petalAngle) * (14.0 + currentEnemy.spawnHint * 6.0);
                        g.lineStyle(3.0, ink, 0.9, true);
                        g.beginFill(baseShade, 0.78);
                        g.drawCircle(petalX, petalY, 10.0 + currentEnemy.spawnHint * 4.0);
                        g.endFill();
                    }
                    g.lineStyle(4.0, ink, 0.94, true);
                    g.beginFill(lightenColor(accentColor, 0.08), 0.36 + currentEnemy.spawnHint * 0.20);
                    g.drawCircle(centerX, centerY, 24.0 + currentEnemy.spawnHint * 10.0);
                    g.endFill();
                    break;
                case 3:
                    g.lineStyle(5, accentColor, 0.72);
                    g.drawCircle(centerX, centerY, 30.0 + currentEnemy.spawnHint * 10.0);
                    g.lineStyle(3, accentColor, 0.52);
                    g.drawCircle(centerX + Math.cos(currentEnemy.phase) * 14.0, centerY - Math.sin(currentEnemy.phase) * 8.0, 18.0 + currentEnemy.spawnHint * 6.0);
                    g.beginFill(baseColor, 0.54);
                    drawBurst(g, centerX, centerY, 24.0 + currentEnemy.spawnHint * 7.0, 10.0 + currentEnemy.spawnHint * 4.0, 4, currentEnemy.phase);
                    g.endFill();
                    break;
                default:
                    g.lineStyle(3.5, ink, 0.92, true);
                    g.beginFill(baseShade, 0.68);
                    g.drawCircle(centerX - 15.0, centerY, 14.0 + currentEnemy.spawnHint * 3.0);
                    g.drawCircle(centerX + 15.0, centerY, 14.0 + currentEnemy.spawnHint * 3.0);
                    g.drawCircle(centerX, centerY - 14.0, 12.0 + currentEnemy.spawnHint * 4.0);
                    g.endFill();
                    g.lineStyle(3, accentColor, 0.76);
                    drawBurst(g, centerX, centerY, 34.0 + currentEnemy.spawnHint * 10.0, 18.0 + currentEnemy.spawnHint * 5.0, 5, currentEnemy.phase * 0.6);
                    break;
            }

            g.lineStyle(2.6, ink, 0.95, true);
            g.beginFill(0xFFF7DE, 0.92);
            g.drawCircle(centerX, centerY, 11.0 + currentEnemy.spawnHint * 4.0);
            g.endFill();
            g.lineStyle(2, 0xFFFDF0, 0.85);
            g.drawCircle(centerX, centerY, 26.0 + currentEnemy.spawnHint * 10.0);

            if (currentEnemy.defeated) {
                g.lineStyle(4, 0xFFF8E6, currentEnemy.explosion);
                g.drawCircle(centerX, centerY, 44.0 + currentEnemy.explosion * 90.0);
                g.lineStyle(2, 0xFFB768, currentEnemy.explosion * 0.8);
                g.drawCircle(centerX, centerY, 28.0 + currentEnemy.explosion * 54.0);
            }
        }

        private function renderPlayer():void {
            var g:Graphics = playerLayer.graphics;
            var baseX:Number = 206.0;
            var baseY:Number = 340.0;
            var bob:Number = Math.sin(songTime * 4.0) * 5.0;
            var headX:Number = baseX + Math.cos(playerPoseAngle) * 12.0;
            var headY:Number = baseY - 118.0 + bob * 0.4;
            var handRadius:Number = 58.0 + outfitTier * 4.0;
            var footRadius:Number = 52.0 + outfitTier * 3.0;
            var leftHandX:Number = baseX + Math.cos(playerPoseAngle + 2.4) * handRadius;
            var leftHandY:Number = baseY - 26.0 + Math.sin(playerPoseAngle + 2.4) * 24.0;
            var rightHandX:Number = baseX + Math.cos(playerPoseAngle - 0.7) * handRadius;
            var rightHandY:Number = baseY - 18.0 + Math.sin(playerPoseAngle - 0.7) * 24.0;
            var leftFootX:Number = baseX + Math.cos(playerPoseAngle + 2.2) * footRadius;
            var leftFootY:Number = baseY + 88.0 + Math.sin(playerPoseAngle + 2.2) * 18.0;
            var rightFootX:Number = baseX + Math.cos(playerPoseAngle - 0.9) * footRadius;
            var rightFootY:Number = baseY + 90.0 + Math.sin(playerPoseAngle - 0.9) * 18.0;
            var dressColor:uint = spectralColor(0.58 + dressCharge * 0.004 + songTime * 0.05, 0.95);
            var accentColor:uint = spectralColor(0.83 + songTime * 0.08, 1.0);
            var waistY:Number = baseY - 18.0;
            var ink:uint = 0x0F0F0F;
            var dressShadow:uint = darkenColor(dressColor, 0.34);
            var dressHighlight:uint = lightenColor(dressColor, 0.26);

            g.clear();
            g.lineStyle(4.5, ink, 0.90, true);
            g.beginFill(0x243A63, 0.10 + spectralPulse * 0.08 + finisherBloom * 0.06);
            g.drawCircle(baseX, baseY - 18.0, 96.0 + sparkleFlash * 22.0);
            g.endFill();

            g.lineStyle(4, accentColor, 0.24 + spectralPulse * 0.24);
            drawRibbon(g, baseX - 8.0, waistY - 10.0, leftHandX, leftHandY, 0.75, accentColor, 0.34 + sparkleFlash * 0.18, 4.0);
            drawRibbon(g, baseX + 8.0, waistY - 8.0, rightHandX, rightHandY, -0.75, accentColor, 0.34 + sparkleFlash * 0.18, 4.0);
            drawRibbon(g, baseX - 10.0, baseY + 18.0, leftFootX, leftFootY, 0.42, dressColor, 0.28 + spectralPulse * 0.14, 5.0);
            drawRibbon(g, baseX + 10.0, baseY + 18.0, rightFootX, rightFootY, -0.42, dressColor, 0.28 + spectralPulse * 0.14, 5.0);

            if (outfitTier >= 1) {
                g.beginFill(accentColor, 0.70);
                g.moveTo(baseX - 40.0, baseY - 56.0);
                g.lineTo(baseX + 8.0, baseY - 84.0);
                g.lineTo(baseX + 46.0, baseY - 50.0);
                g.lineTo(baseX + 12.0, baseY - 26.0);
                g.lineTo(baseX - 34.0, baseY - 30.0);
                g.lineTo(baseX - 40.0, baseY - 56.0);
                g.endFill();
            }

            if (outfitTier >= 2) {
                g.beginFill(dressColor, 0.74);
                g.moveTo(baseX - 54.0, baseY + 36.0);
                g.lineTo(baseX, baseY + 106.0);
                g.lineTo(baseX + 54.0, baseY + 36.0);
                g.lineTo(baseX, baseY + 8.0);
                g.lineTo(baseX - 54.0, baseY + 36.0);
                g.endFill();

                g.beginFill(accentColor, 0.48);
                g.moveTo(baseX - 24.0, baseY + 22.0);
                g.lineTo(baseX - 4.0, baseY + 94.0);
                g.lineTo(baseX - 44.0, baseY + 54.0);
                g.lineTo(baseX - 24.0, baseY + 22.0);
                g.moveTo(baseX + 24.0, baseY + 22.0);
                g.lineTo(baseX + 4.0, baseY + 94.0);
                g.lineTo(baseX + 44.0, baseY + 54.0);
                g.lineTo(baseX + 24.0, baseY + 22.0);
                g.endFill();
            }

            if (outfitTier >= 3) {
                g.lineStyle(4, accentColor, 0.62);
                g.moveTo(headX - 34.0, headY - 8.0);
                g.lineTo(leftHandX, leftHandY);
                g.moveTo(headX + 34.0, headY - 6.0);
                g.lineTo(rightHandX, rightHandY);
                g.lineStyle(3, accentColor, 0.52);
                drawRibbon(g, baseX - 20.0, baseY - 68.0, baseX - 64.0, baseY + 8.0, 0.95, accentColor, 0.46, 3.0);
                drawRibbon(g, baseX + 20.0, baseY - 68.0, baseX + 64.0, baseY + 8.0, -0.95, accentColor, 0.46, 3.0);
            }

            if (outfitTier >= 4) {
                g.lineStyle(3, 0xFFF7D1, 0.82);
                g.drawCircle(headX, headY - 8.0, 26.0 + sparkleFlash * 8.0);
                g.lineStyle(2, 0xFFF7D1, 0.68);
                drawBurst(g, headX, headY - 26.0, 18.0 + sparkleFlash * 6.0, 8.0, 5, songTime * 0.8);
            }

            g.lineStyle(5.0, ink, 0.94, true);
            g.beginFill(dressShadow, 0.94);
            g.drawRoundRect(baseX - 28.0, baseY - 72.0, 56.0, 96.0, 18.0, 18.0);
            g.endFill();

            g.lineStyle(0, 0, 0);
            g.beginFill(dressHighlight, 0.56);
            g.drawRoundRect(baseX - 22.0, baseY - 66.0, 20.0, 78.0, 12.0, 12.0);
            g.endFill();

            g.beginFill(0x10223F, 0.42);
            g.drawRoundRect(baseX - 18.0, baseY - 52.0, 36.0, 46.0, 14.0, 14.0);
            g.endFill();
            g.beginFill(accentColor, 0.64);
            drawBurst(g, baseX, baseY - 30.0, 10.0 + spectralPulse * 3.0, 4.0, 4, songTime * 1.2);
            g.endFill();

            g.lineStyle(3.0, ink, 0.95, true);
            g.beginFill(0x9FC4F4, 0.94);
            g.drawCircle(headX, headY, 26.0);
            g.drawCircle(leftHandX, leftHandY, 12.0);
            g.drawCircle(rightHandX, rightHandY, 12.0);
            g.drawCircle(leftFootX, leftFootY, 14.0);
            g.drawCircle(rightFootX, rightFootY, 14.0);
            g.endFill();

            g.lineStyle(0, 0, 0);
            g.beginFill(0xDCEBFF, 0.54);
            g.drawCircle(headX - 8.0, headY - 9.0, 8.0);
            g.endFill();
            g.beginFill(0x0B1730, 0.88);
            g.drawCircle(headX - 7.0, headY - 3.0, 2.5);
            g.drawCircle(headX + 7.0, headY - 3.0, 2.5);
            g.endFill();
            g.lineStyle(2, 0xEAF6FF, 0.74);
            g.moveTo(headX - 6.0, headY + 8.0);
            g.curveTo(headX, headY + 12.0 + Math.sin(songTime * 3.0) * 2.0, headX + 6.0, headY + 8.0);

            if (lockReady) {
                var targetX:Number = baseX + Math.cos(lockTargetAngle) * 74.0;
                var targetY:Number = baseY - 12.0 + Math.sin(lockTargetAngle) * 64.0;
                g.lineStyle(3, 0xFFF4C4, 0.9);
                g.drawCircle(baseX, baseY - 12.0, 78.0);
                g.lineStyle(2, 0xFFB768, 0.95);
                g.moveTo(baseX, baseY - 12.0);
                g.lineTo(targetX, targetY);
                g.lineStyle(2, 0xFFF4C4, 0.42);
                g.drawCircle(targetX, targetY, 18.0 + finisherBloom * 16.0);
                g.beginFill(0xFFF0D0, 0.95);
                g.drawCircle(targetX, targetY, 7.0);
                g.endFill();
            }
        }

        private function renderParticles():void {
            var g:Graphics = particleLayer.graphics;
            g.clear();

            for each (var particle:SparkleParticle in particles) {
                g.beginFill(particle.color, particle.life);
                g.drawCircle(particle.x, particle.y, particle.size * particle.life);
                g.endFill();
            }
        }

        private function updateHud():void {
            titleField.text = title;
            scoreField.text = "Score " + score + "   Combo " + combo + "   Beat " + beatIndex;
            comboField.text = "Cue: " + lastCueHint;
            wardrobeField.text = "Sparkle wardrobe tier: " + wardrobeLabel() + "   Dress charge: " + int(dressCharge) + "%   Matter disruption: " + int(matterDisruption * 100.0) + "%";
            enemyField.text = currentEnemy ? ("LiteMite swarm: " + currentEnemy.name + "   Telegraph: " + laneGlyphs[currentEnemy.telegraphLane] + "   Tail integrity: " + int(Math.max(0.0, currentEnemy.integrity) * 100.0) + "%   Emberence: " + int(currentEnemy.spawnHint * 100.0) + "%") : "No LiteMite swarm active.";
            lockField.text = lockReady ? ("POSE LOCK :: " + poseName(lockTargetAngle) + " :: " + int(lockTimer * 100.0) / 100.0 + "s") : "POSE LOCK :: building";
            if (tutorialActive) {
                helpField.text = tutorialHelpLine();
                systemField.text = tutorialSystemLine();
            } else {
                helpField.text = "Controls: A / S / K / L or arrows for the four dance seams, SPACE to lock a pose once the tail destabilizes.";
                systemField.text = "Prototype systems: procedural dubstep, adaptive framebuffer, archetyped LiteMites, lane sigils, outfit ribbons, and pose-lock finish art.";
            }
        }

        private function updateTutorialBeat():void {
            if (tutorialStep < 4) {
                refreshTutorialPrompt();
                return;
            }

            if (tutorialStep < 6) {
                if (cues.length == 0) {
                    spawnTutorialCue((tutorialStep + beatIndex) % LANE_COUNT);
                }
                return;
            }

            if (!lockReady) {
                startPoseLock();
            }
            lockTimer = Math.max(lockTimer, beatDuration * 4.0);
            lockTargetAngle = playerPoseAngle;
            refreshTutorialPrompt();
        }

        private function handleTutorialLanePrimer(lane:int):void {
            var expectedLane:int = tutorialStep;
            targetPoseAngle = poseAngleForLane(lane);

            if (lane != expectedLane) {
                lastCueHint = "Tutorial: Step " + (tutorialStep + 1) + " -> tap " + laneGlyphs[expectedLane] + " (" + laneKeyHint(expectedLane) + ")";
                return;
            }

            tutorialStep++;
            sparkTutorialBurst(lane);
            refreshTutorialPrompt();
        }

        private function onTutorialCueScored():void {
            if (tutorialStep < 4 || tutorialStep > 5) {
                return;
            }

            tutorialCueHits++;
            if (tutorialCueHits >= 2) {
                tutorialStep = 6;
                cues = [];
            } else {
                tutorialStep = 5;
            }
            refreshTutorialPrompt();
        }

        private function spawnTutorialCue(lane:int):void {
            var cue:DanceCue = new DanceCue();
            cue.lane = lane;
            cue.y = -40.0;
            cue.speed = 172.0;
            cue.color = laneColor(cue.lane);
            cue.size = 22.0;
            cue.wobble = pseudo(beatIndex * 2.17 + lane) * Math.PI * 2.0;
            cue.anticipation = 0.5;
            cue.form = lane % 4;
            cue.spin = 0.25;
            cue.trail = 26.0;
            cues.push(cue);
            lastCueHint = "Tutorial: strike " + laneNames[lane] + " when it reaches the line.";
        }

        private function sparkTutorialBurst(lane:int):void {
            emitBurst(Number(laneCenters[lane]), STRIKE_Y, laneColor(lane), 8, true);
        }

        private function refreshTutorialPrompt():void {
            switch (tutorialStep) {
                case 0:
                    lastCueHint = "Tutorial 1/7: tap Head Flick once (A or Left).";
                    break;
                case 1:
                    lastCueHint = "Tutorial 2/7: tap Torso Pulse once (S or Down).";
                    break;
                case 2:
                    lastCueHint = "Tutorial 3/7: tap Hand Halo once (K or Up).";
                    break;
                case 3:
                    lastCueHint = "Tutorial 4/7: tap Foot Spark once (L or Right).";
                    break;
                case 4:
                    lastCueHint = "Tutorial 5/7: hit one incoming cue on the strike line.";
                    break;
                case 5:
                    lastCueHint = "Tutorial 6/7: hit one more cue to build the lock window.";
                    break;
                case 6:
                    lastCueHint = "Tutorial 7/7: hold any silhouette and press SPACE to pose-lock.";
                    break;
                default:
                    break;
            }
        }

        private function tutorialHelpLine():String {
            switch (tutorialStep) {
                case 0:
                    return "Tutorial Step 1: Press A or Left for Head Flick.";
                case 1:
                    return "Tutorial Step 2: Press S or Down for Torso Pulse.";
                case 2:
                    return "Tutorial Step 3: Press K or Up for Hand Halo.";
                case 3:
                    return "Tutorial Step 4: Press L or Right for Foot Spark.";
                case 4:
                    return "Tutorial Step 5: Time the cue to the glowing strike line.";
                case 5:
                    return "Tutorial Step 6: Land one more cue to prime pose lock.";
                case 6:
                    return "Tutorial Step 7: Hold a pose direction and press SPACE.";
            }
            return "Tutorial complete. Freestyle all lanes and finishers.";
        }

        private function tutorialSystemLine():String {
            return "Guided flow active: " + (tutorialStep + 1) + "/7 action-by-action lane training.";
        }

        private function laneKeyHint(lane:int):String {
            switch (lane) {
                case 0:
                    return "A/Left";
                case 1:
                    return "S/Down";
                case 2:
                    return "K/Up";
                case 3:
                    return "L/Right";
            }
            return "?";
        }

        private function renderDiamondLabel():String {
            return lockReady ? poseName(lockTargetAngle) : "Weave the seams";
        }

        private function poseAngleForLane(lane:int):Number {
            switch (lane) {
                case 0:
                    return -2.25;
                case 1:
                    return -1.10;
                case 2:
                    return 0.62;
                case 3:
                    return 1.85;
            }
            return 0.0;
        }

        private function poseName(angle:Number):String {
            var normalized:Number = normalizeAngle(angle);
            if (normalized < Math.PI * 0.5) {
                return "Halo Bow";
            }
            if (normalized < Math.PI) {
                return "Prism Lean";
            }
            if (normalized < Math.PI * 1.5) {
                return "Orbit Fold";
            }
            return "Nova Kick";
        }

        private function wardrobeLabel():String {
            switch (outfitTier) {
                case 1:
                    return "Pulse Sash";
                case 2:
                    return "Prism Skirt";
                case 3:
                    return "Halo Rig";
                case 4:
                    return "Light Envisioned";
            }
            return "BlueNoMid Base";
        }

        private function drawDiamond(graphicsTarget:Graphics, xPos:Number, yPos:Number, size:Number):void {
            graphicsTarget.moveTo(xPos, yPos - size);
            graphicsTarget.lineTo(xPos + size, yPos);
            graphicsTarget.lineTo(xPos, yPos + size);
            graphicsTarget.lineTo(xPos - size, yPos);
            graphicsTarget.lineTo(xPos, yPos - size);
        }

        private function drawBurst(graphicsTarget:Graphics, xPos:Number, yPos:Number, outer:Number, inner:Number, points:int, rotation:Number):void {
            var firstX:Number = xPos + Math.cos(rotation - Math.PI * 0.5) * outer;
            var firstY:Number = yPos + Math.sin(rotation - Math.PI * 0.5) * outer;
            graphicsTarget.moveTo(firstX, firstY);
            for (var pointIndex:int = 1; pointIndex < points * 2; pointIndex++) {
                var radius:Number = pointIndex % 2 == 0 ? outer : inner;
                var angle:Number = rotation - Math.PI * 0.5 + pointIndex * Math.PI / points;
                graphicsTarget.lineTo(xPos + Math.cos(angle) * radius, yPos + Math.sin(angle) * radius);
            }
            graphicsTarget.lineTo(firstX, firstY);
        }

        private function drawChevron(graphicsTarget:Graphics, xPos:Number, yPos:Number, width:Number, height:Number):void {
            graphicsTarget.moveTo(xPos - width, yPos - height * 0.55);
            graphicsTarget.lineTo(xPos - width * 0.18, yPos);
            graphicsTarget.lineTo(xPos - width, yPos + height * 0.55);
            graphicsTarget.lineTo(xPos + width, yPos + height * 0.18);
            graphicsTarget.lineTo(xPos + width * 0.24, yPos);
            graphicsTarget.lineTo(xPos + width, yPos - height * 0.18);
            graphicsTarget.lineTo(xPos - width, yPos - height * 0.55);
        }

        private function drawRibbon(graphicsTarget:Graphics, startX:Number, startY:Number, endX:Number, endY:Number, bend:Number, color:uint, alpha:Number, thickness:Number):void {
            var midX:Number = (startX + endX) * 0.5 + (endY - startY) * 0.24 * bend;
            var midY:Number = (startY + endY) * 0.5 - (endX - startX) * 0.18 * bend;
            graphicsTarget.lineStyle(thickness, color, alpha, true);
            graphicsTarget.moveTo(startX, startY);
            graphicsTarget.curveTo(midX, midY, endX, endY);
        }

        private function drawCueShape(graphicsTarget:Graphics, cue:DanceCue, xPos:Number, yPos:Number, size:Number):void {
            switch (cue.form) {
                case 1:
                    drawChevron(graphicsTarget, xPos, yPos, size, size * 0.9);
                    break;
                case 2:
                    drawBurst(graphicsTarget, xPos, yPos, size * 1.05, size * 0.42, 6, cue.wobble + songTime * cue.spin * 0.6);
                    break;
                case 3:
                    drawBurst(graphicsTarget, xPos, yPos, size * 1.12, size * 0.58, 5, cue.wobble - songTime * cue.spin * 0.4);
                    break;
                case 0:
                default:
                    drawDiamond(graphicsTarget, xPos, yPos, size);
                    break;
            }
        }

        private function drawLaneSigil(graphicsTarget:Graphics, xPos:Number, yPos:Number, lane:int, scale:Number, alpha:Number):void {
            graphicsTarget.lineStyle(2, laneColor(lane), alpha, true);
            switch (lane) {
                case 0:
                    drawChevron(graphicsTarget, xPos, yPos, scale, scale * 0.72);
                    break;
                case 1:
                    graphicsTarget.moveTo(xPos - scale, yPos - scale * 0.55);
                    graphicsTarget.lineTo(xPos + scale, yPos - scale * 0.55);
                    graphicsTarget.moveTo(xPos - scale, yPos);
                    graphicsTarget.lineTo(xPos + scale, yPos);
                    graphicsTarget.moveTo(xPos - scale, yPos + scale * 0.55);
                    graphicsTarget.lineTo(xPos + scale, yPos + scale * 0.55);
                    break;
                case 2:
                    graphicsTarget.drawCircle(xPos, yPos, scale * 0.72);
                    graphicsTarget.moveTo(xPos - scale * 0.28, yPos);
                    graphicsTarget.lineTo(xPos + scale * 0.28, yPos);
                    graphicsTarget.moveTo(xPos, yPos - scale * 0.28);
                    graphicsTarget.lineTo(xPos, yPos + scale * 0.28);
                    break;
                case 3:
                    drawBurst(graphicsTarget, xPos, yPos, scale, scale * 0.42, 4, songTime * 0.4);
                    break;
            }
        }

        private function archetypeCoreColor(index:int):uint {
            switch (index) {
                case 0:
                    return 0xFFE58C;
                case 1:
                    return 0xFF9F72;
                case 2:
                    return 0xFFF2C8;
                case 3:
                    return 0xD8B8FF;
                case 4:
                    return 0x9DE1FF;
            }
            return 0xFFECA4;
        }

        private function archetypeAccentColor(index:int):uint {
            switch (index) {
                case 0:
                    return 0xFFB85A;
                case 1:
                    return 0xFF6C54;
                case 2:
                    return 0xFFEFA2;
                case 3:
                    return 0xA87BFF;
                case 4:
                    return 0x6CD6FF;
            }
            return 0x84E4FF;
        }

        private function laneColor(lane:int):uint {
            switch (lane) {
                case 0:
                    return 0x7CE7FF;
                case 1:
                    return 0x9A92FF;
                case 2:
                    return 0xFF81C9;
                case 3:
                    return 0xFFB75E;
            }
            return 0xFFFFFF;
        }

        private function spectralColor(phase:Number, brightness:Number):uint {
            phase -= Math.floor(phase);
            var red:int = clampByte((0.5 + 0.5 * Math.sin((phase + 0.00) * Math.PI * 2.0)) * 255.0 * brightness);
            var green:int = clampByte((0.5 + 0.5 * Math.sin((phase + 0.33) * Math.PI * 2.0)) * 255.0 * brightness);
            var blue:int = clampByte((0.5 + 0.5 * Math.sin((phase + 0.66) * Math.PI * 2.0)) * 255.0 * brightness);
            return (red << 16) | (green << 8) | blue;
        }

        private function darkenColor(color:uint, amount:Number):uint {
            var red:int = clampByte(((color >> 16) & 0xFF) * (1.0 - amount));
            var green:int = clampByte(((color >> 8) & 0xFF) * (1.0 - amount));
            var blue:int = clampByte((color & 0xFF) * (1.0 - amount));
            return (red << 16) | (green << 8) | blue;
        }

        private function lightenColor(color:uint, amount:Number):uint {
            var red:int = clampByte(((color >> 16) & 0xFF) + (255 - ((color >> 16) & 0xFF)) * amount);
            var green:int = clampByte(((color >> 8) & 0xFF) + (255 - ((color >> 8) & 0xFF)) * amount);
            var blue:int = clampByte((color & 0xFF) + (255 - (color & 0xFF)) * amount);
            return (red << 16) | (green << 8) | blue;
        }

        private function posterizeChannel(value:int, levels:Number):int {
            if (levels <= 1.0) {
                return clampByte(value);
            }
            var step:Number = 255.0 / levels;
            return clampByte(int(value / step) * step);
        }

        private function normalizeAngle(value:Number):Number {
            while (value < 0.0) {
                value += Math.PI * 2.0;
            }
            while (value >= Math.PI * 2.0) {
                value -= Math.PI * 2.0;
            }
            return value;
        }

        private function shortestAngle(from:Number, to:Number):Number {
            var delta:Number = normalizeAngle(to) - normalizeAngle(from);
            if (delta > Math.PI) {
                delta -= Math.PI * 2.0;
            }
            if (delta < -Math.PI) {
                delta += Math.PI * 2.0;
            }
            return delta;
        }

        private function envelopeFromTrigger(beatPosition:Number, trigger:Number, decay:Number):Number {
            var delta:Number = beatPosition - trigger;
            while (delta < 0.0) {
                delta += 4.0;
            }
            return Math.max(0.0, 1.0 - delta / decay);
        }

        private function gridEnvelope(gridPosition:Number, decay:Number):Number {
            var phase:Number = gridPosition - Math.floor(gridPosition);
            return Math.max(0.0, 1.0 - phase / decay);
        }

        private function randomNoise(seed:int):Number {
            var value:Number = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
            return (value - Math.floor(value)) * 2.0 - 1.0;
        }

        private function pseudo(seed:Number):Number {
            var value:Number = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
            return value - Math.floor(value);
        }

        private function clampByte(value:Number):int {
            if (value < 0.0) {
                return 0;
            }
            if (value > 255.0) {
                return 255;
            }
            return int(value);
        }

        private function clampAudio(value:Number):Number {
            if (value < -1.0) {
                return -1.0;
            }
            if (value > 1.0) {
                return 1.0;
            }
            return value;
        }
    }

}
