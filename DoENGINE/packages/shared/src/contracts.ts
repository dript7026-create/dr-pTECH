export interface DoTraceRecord {
    timestamp: string;
    doer: string;
    motif: string;
    vibe: string;
    action: string;
    hardware: string;
}

export interface TraceWriteResult {
    filename: string;
    roots: string[];
}

export interface PipelineAssetRecord {
    assetId: string;
    category: string;
    sourcePath: string;
    derivedOutputs?: string[];
}

export interface DoNowRuntimeEntry {
    assetId: string;
    category: string;
    runtimeBucket: string;
    sourcePath: string;
    immediateReady: boolean;
    generatedOutputs: string[];
}

export interface DoNowRuntimeManifest {
    projectName: string;
    streamName: string;
    immediateFunctionality: string[];
    preloadGroups: Array<{ name: string; matchBuckets: string[] }>;
    entries: DoNowRuntimeEntry[];
}

export interface HardwareSignatureProvider {
    (): string;
}

export interface SessionKeyProvider {
    (): string;
}

export enum BangoPlatformKind {
    WINDOWS = 0,
    N3DS = 1,
    IDTECH2 = 2,
}

export const BANGO_BUTTON = {
    ATTACK_LIGHT: 1 << 0,
    ATTACK_HEAVY: 1 << 1,
    JUMP: 1 << 2,
    CROUCH_SLIDE: 1 << 3,
    HEAL: 1 << 4,
    BLOCK: 1 << 5,
    PARRY: 1 << 6,
    FOCUS_LOCK: 1 << 7,
    MENU: 1 << 8,
    GAME_MENU: 1 << 9,
    INTERACT_MASS: 1 << 10,
    SPECIAL_WHEEL: 1 << 11,
    SPRINT: 1 << 12,
} as const;

export interface BangoTelemetryConsent {
    localOnly: boolean;
    allowCamera: boolean;
    allowMicrophone: boolean;
    allowEnvironmentalInference: boolean;
}

export interface BangoTelemetrySample {
    ambientLuma: number;
    ambientMotion: number;
    ambientAudioLevel: number;
    playerVoiceEnergy: number;
    playerBreathProxy: number;
    playerFocusProxy: number;
}

export interface BangoInputFrame {
    moveX: number;
    moveY: number;
    lookX: number;
    lookY: number;
    buttonsHeld: number;
    buttonsPressed: number;
    hapticPressureLeft: number;
    hapticPressureRight: number;
    touchActive: boolean;
    touchX: number;
    touchY: number;
    stereoDepthStrength: number;
}

export interface BangoDoEngineBridgeState {
    tension: number;
    pressure: number;
    temperature: number;
    mass: number;
    velocity: number;
}

export interface BangoEngineTargetConfig {
    platform: BangoPlatformKind;
    requireNew3ds: boolean;
    enableStereoDepth: boolean;
    enableTouchControls: boolean;
    enableControllerSupport: boolean;
    telemetry: BangoTelemetryConsent;
}

export interface BangoEngineTargetState {
    config: BangoEngineTargetConfig;
    frame: BangoInputFrame;
    telemetry: BangoTelemetrySample;
    doengine: BangoDoEngineBridgeState;
    combatPrecision: number;
    combatForce: number;
    movementWeightRelief: number;
    environmentalIntensity: number;
}

export interface HybridRenderStage {
    id: string;
    label: string;
    owner: 'DoENGINE' | 'ORBEngine' | 'PlayNOW' | 'GameProfile' | 'DODO3D';
    description: string;
}

export interface HybridShaderPass {
    id: string;
    label: string;
    role: string;
}

export interface HybridShaderProgram {
    backend: string;
    look: string;
    passes: HybridShaderPass[];
    uniforms: Record<string, number>;
    asset_loaders?: string[];
    script_capabilities?: string[];
}

export interface HybridControllerActionBinding {
    actionId: string;
    label: string;
    inputs: string[];
    gameplayContext: string;
}

export interface HybridControllerProfile {
    profileId: string;
    label: string;
    deviceClass: 'xinput' | 'keyboard-mouse' | 'touch' | 'generic-gamepad';
    bindings: HybridControllerActionBinding[];
}

export interface HybridGameProfile {
    gameId: string;
    label: string;
    renderMode: 'full3d-pseudo3d-hybrid';
    playnowManifest?: string;
    tutorialSpec?: string;
    controllerProfileId: string;
    supports: string[];
}

export interface HybridEngineRuntimeProfile {
    runtimeId: string;
    label: string;
    rendererPhilosophy: string;
    rendererBackend?: string;
    renderStages: HybridRenderStage[];
    controllerProfiles: HybridControllerProfile[];
    games: HybridGameProfile[];
    shaderProgram?: HybridShaderProgram;
}

export type ResonanceBandRole = 'direct-control' | 'game-logic' | 'menu-loadout';

export type ResonanceBandSource =
    | 'desktop-telemetry'
    | 'camera-proxy'
    | 'microphone-proxy'
    | 'ppg'
    | 'gsr'
    | 'imu'
    | 'dry-eeg'
    | 'ear-eeg'
    | 'controller-cadence';

export interface ResonanceBandWindow {
    id: string;
    label: string;
    role: ResonanceBandRole;
    nominalHzLow: number;
    nominalHzHigh: number;
    source: ResonanceBandSource;
    confidenceGate: number;
    note: string;
}

export interface ResonanceSignalQuality {
    source: ResonanceBandSource;
    quality: number;
    confidence: number;
    enabled: boolean;
}

export interface HapticFiberChannel {
    channelId: string;
    label: string;
    placement: 'left-grip' | 'right-grip' | 'shoulder-band' | 'seat' | 'desk' | 'wearable';
    amplitude: number;
    carrierHz: number;
    envelopeMs: number;
    dutyCycleLimit: number;
}

export interface HapticFeedbackProfile {
    profileId: string;
    label: string;
    channels: HapticFiberChannel[];
    overloadClamp: number;
    notes: string[];
}

export interface ResonanceInputRoute {
    routeId: string;
    label: string;
    role: ResonanceBandRole;
    target: string;
    smoothingMs: number;
    deadzone: number;
    confidenceGate: number;
    fallback: string;
}

export interface WirelessIsolationProfile {
    profileId: string;
    label: string;
    bluetoothAllowed: boolean;
    wifiAllowed: boolean;
    requirePairingHandshake: boolean;
    rotateSessionKeys: boolean;
    localOnlyControlPlane: boolean;
    allowInboundRemoteControl: boolean;
    sensorBusSegregated: boolean;
    notes: string[];
}

export interface AdaptiveConsentProfile {
    localOnly: boolean;
    allowCamera: boolean;
    allowMicrophone: boolean;
    allowWearables: boolean;
    allowSpectralAccessory: boolean;
    retainRawSignals: boolean;
    retainDerivedSignals: boolean;
}

export interface AdaptiveRuntimeProfile {
    profileId: string;
    label: string;
    platform: 'nanoplayt' | 'playhub' | 'desktop-demo';
    powerMode: 'battery-disciplined' | 'balanced' | 'desktop';
    consent: AdaptiveConsentProfile;
    bandWindows: ResonanceBandWindow[];
    inputRoutes: ResonanceInputRoute[];
    haptics: HapticFeedbackProfile;
    wirelessIsolation: WirelessIsolationProfile;
    notes: string[];
}

export interface AdaptiveRuntimeState {
    profileId: string;
    receptivityScore: number;
    cognitiveLoadScore: number;
    stressActivationScore: number;
    fatigueScore: number;
    engagementScore: number;
    confidence: number;
    signalQuality: ResonanceSignalQuality[];
    adaptationRecommendations: string[];
}