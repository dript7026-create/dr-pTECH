import {
    BangoEngineTargetConfig,
    BangoEngineTargetState,
    BangoInputFrame,
    BangoPlatformKind,
    BangoTelemetrySample,
} from '../../shared/src/contracts';

function clamp(value: number, minimum: number, maximum: number): number {
    return Math.min(Math.max(value, minimum), maximum);
}

function createEmptyFrame(): BangoInputFrame {
    return {
        moveX: 0,
        moveY: 0,
        lookX: 0,
        lookY: 0,
        buttonsHeld: 0,
        buttonsPressed: 0,
        hapticPressureLeft: 0,
        hapticPressureRight: 0,
        touchActive: false,
        touchX: 0,
        touchY: 0,
        stereoDepthStrength: 0,
    };
}

export function createEmptyTelemetry(): BangoTelemetrySample {
    return {
        ambientLuma: 0,
        ambientMotion: 0,
        ambientAudioLevel: 0,
        playerVoiceEnergy: 0,
        playerBreathProxy: 0,
        playerFocusProxy: 0,
    };
}

export function createDefaultConfig(platform: BangoPlatformKind): BangoEngineTargetConfig {
    return {
        platform,
        requireNew3ds: platform === BangoPlatformKind.N3DS,
        enableStereoDepth: platform === BangoPlatformKind.N3DS,
        enableTouchControls: platform === BangoPlatformKind.N3DS,
        enableControllerSupport: true,
        telemetry: {
            localOnly: true,
            allowCamera: false,
            allowMicrophone: false,
            allowEnvironmentalInference: false,
        },
    };
}

export function createEngineTargetState(config?: Partial<BangoEngineTargetConfig>): BangoEngineTargetState {
    const baseConfig = createDefaultConfig(config?.platform ?? BangoPlatformKind.WINDOWS);
    return {
        config: {
            ...baseConfig,
            ...config,
            telemetry: {
                ...baseConfig.telemetry,
                ...config?.telemetry,
            },
        },
        frame: createEmptyFrame(),
        telemetry: createEmptyTelemetry(),
        doengine: {
            tension: 0,
            pressure: 0,
            temperature: 0,
            mass: 0,
            velocity: 0,
        },
        combatPrecision: 0,
        combatForce: 0,
        movementWeightRelief: 0,
        environmentalIntensity: 0,
    };
}

export function beginFrame(state: BangoEngineTargetState): void {
    state.frame = {
        ...createEmptyFrame(),
        buttonsHeld: state.frame.buttonsHeld,
    };
}

export function ingestTouch(state: BangoEngineTargetState, active: boolean, x: number, y: number): void {
    state.frame.touchActive = active;
    state.frame.touchX = x;
    state.frame.touchY = y;
}

export function ingestAnalog(
    state: BangoEngineTargetState,
    moveX: number,
    moveY: number,
    lookX: number,
    lookY: number,
): void {
    state.frame.moveX = clamp(moveX, -1, 1);
    state.frame.moveY = clamp(moveY, -1, 1);
    state.frame.lookX = clamp(lookX, -1, 1);
    state.frame.lookY = clamp(lookY, -1, 1);
}

export function ingestButtons(state: BangoEngineTargetState, buttonsHeld: number, buttonsPressed: number): void {
    state.frame.buttonsHeld = buttonsHeld;
    state.frame.buttonsPressed = buttonsPressed;
}

export function ingestHaptics(state: BangoEngineTargetState, leftForce: number, rightForce: number): void {
    state.frame.hapticPressureLeft = clamp(leftForce, 0, 1);
    state.frame.hapticPressureRight = clamp(rightForce, 0, 1);
}

export function ingestStereo(state: BangoEngineTargetState, sliderState: number): void {
    state.frame.stereoDepthStrength = clamp(sliderState, 0, 1);
}

export function ingestTelemetry(state: BangoEngineTargetState, sample: BangoTelemetrySample): void {
    if (!state.config.telemetry.localOnly) {
        return;
    }

    state.telemetry = { ...sample };
}

export function updateState(state: BangoEngineTargetState, dt: number): BangoEngineTargetState {
    const movement = Math.sqrt(state.frame.moveX * state.frame.moveX + state.frame.moveY * state.frame.moveY);
    const stickPressure = Math.abs(state.frame.lookX) + Math.abs(state.frame.lookY);

    state.combatPrecision = clamp(
        0.45 + stickPressure * 0.2 + state.frame.hapticPressureRight * 0.25 + state.telemetry.playerFocusProxy * 0.1,
        0,
        1,
    );
    state.combatForce = clamp(
        0.3 + movement * 0.2 + state.frame.hapticPressureLeft * 0.25 + state.frame.hapticPressureRight * 0.25,
        0,
        1,
    );
    state.movementWeightRelief = clamp(
        (state.config.enableTouchControls && state.frame.touchActive ? 0.25 : 0) + state.frame.stereoDepthStrength * 0.15,
        0,
        1,
    );
    state.environmentalIntensity = clamp(
        state.telemetry.ambientLuma * 0.25 +
            state.telemetry.ambientMotion * 0.25 +
            state.telemetry.ambientAudioLevel * 0.25 +
            state.telemetry.playerVoiceEnergy * 0.25,
        0,
        1,
    );

    state.doengine.tension = 0.35 + movement * 0.2 + state.environmentalIntensity * 0.15;
    state.doengine.pressure = 0.4 + state.combatForce * 0.3;
    state.doengine.temperature = 0.3 + state.environmentalIntensity * 0.35;
    state.doengine.mass = 0.5 + state.movementWeightRelief * 0.15;
    state.doengine.velocity = movement * (1 + dt * 0.2);
    return state;
}