import {
	HybridControllerProfile,
	HybridEngineRuntimeProfile,
	HybridGameProfile,
	HybridRenderStage,
	HybridShaderProgram,
} from '../../shared/src/contracts';

const shaderProgram: HybridShaderProgram = {
	backend: 'python-pillow-cpu-raster',
	look: 'illusioncanvas-pseudo3d',
	asset_loaders: ['builtin', 'obj', 'glb', 'billboard', 'scene-manifest'],
	script_capabilities: ['spin', 'bob', 'pulse', 'orbit'],
	passes: [
		{
			id: 'sky-dome-gradient',
			label: 'Sky Dome Gradient',
			role: 'Establishes the amber-jade atmosphere before geometry is drawn.',
		},
		{
			id: 'floor-warp-grid',
			label: 'Floor Warp Grid',
			role: 'Projects the curved stage plane that sells the pseudo-3D IllusionCanvas feel.',
		},
		{
			id: 'lambert-rim-band',
			label: 'Lambert Rim Band',
			role: 'Combines directional light, rim light, and stepped palette shading on mesh faces.',
		},
		{
			id: 'fog-and-aerial-perspective',
			label: 'Fog And Aerial Perspective',
			role: 'Compresses distant contrast so deeper layers feel painterly rather than flat.',
		},
		{
			id: 'scanline-canvas-grain',
			label: 'Scanline Canvas Grain',
			role: 'Adds post-texture, scanline drift, and vignette to keep the output tactile.',
		},
	],
	uniforms: {
		fog_density: 0.26,
		rim_power: 2.4,
		scanline_intensity: 0.18,
		palette_steps: 5,
		floor_curvature: 0.16,
	},
};

const renderStages: HybridRenderStage[] = [
	{
		id: 'scene-ingest',
		label: 'Scene Ingest',
		owner: 'DoENGINE',
		description: 'Resolve manifests, controller profile, telemetry policy, and game-profile feature declarations.',
	},
	{
		id: 'recursive-space-graph',
		label: 'Recursive Space Graph',
		owner: 'ORBEngine',
		description: 'Traverse parent-child space graph, remagnification rules, and pseudo-3D visibility chains.',
	},
	{
		id: 'full-3d-proxy',
		label: 'Full 3D Proxy',
		owner: 'DODO3D',
		description: 'Evaluate mesh-backed transforms, sockets, collision anchors, and authored depth metrics.',
	},
	{
		id: 'pseudo-3d-composite',
		label: 'Pseudo-3D Composite',
		owner: 'DODO3D',
		description: 'Blend floor warp, sprite billboards, top-cap projection, fog, and recursive scene overlays.',
	},
	{
		id: 'ui-and-telemetry',
		label: 'UI And Telemetry',
		owner: 'DoENGINE',
		description: 'Present the DODOGame shell, diagnostics, status cards, and trace-safe runtime feedback.',
	},
	{
		id: 'playnow-staging',
		label: 'PlayNOW Staging',
		owner: 'PlayNOW',
		description: 'Surface tutorial/test manifests, generated bundle references, and automation-facing runtime handoff.',
	},
];

const bangoControllerProfile: HybridControllerProfile = {
	profileId: 'bango-xinput-full',
	label: 'Bango Full XInput',
	deviceClass: 'xinput',
	bindings: [
		{ actionId: 'move', label: 'Move', inputs: ['left_stick'], gameplayContext: 'Traversal' },
		{ actionId: 'camera', label: 'Camera', inputs: ['right_stick'], gameplayContext: 'View' },
		{ actionId: 'jump', label: 'Jump (tap B)', inputs: ['B'], gameplayContext: 'Traversal' },
		{ actionId: 'crouch_slide', label: 'Crouch Or Slide', inputs: ['A'], gameplayContext: 'Traversal' },
		{ actionId: 'sprint', label: 'Sprint (hold B)', inputs: ['B'], gameplayContext: 'Traversal' },
		{ actionId: 'light_attack', label: 'Light Attack', inputs: ['LB'], gameplayContext: 'Combat' },
		{ actionId: 'heavy_attack', label: 'Heavy Attack', inputs: ['RT'], gameplayContext: 'Combat' },
		{ actionId: 'block', label: 'Block', inputs: ['LeftThumb'], gameplayContext: 'Combat' },
		{ actionId: 'parry', label: 'Parry', inputs: ['RightThumb'], gameplayContext: 'Combat' },
		{ actionId: 'ability_wheel', label: 'Ability Wheel', inputs: ['LT', 'right_stick'], gameplayContext: 'Ability' },
		{ actionId: 'face_x', label: 'Face X', inputs: ['X'], gameplayContext: 'Generic' },
		{ actionId: 'face_y', label: 'Face Y', inputs: ['Y'], gameplayContext: 'Generic' },
		{ actionId: 'menu', label: 'Menu', inputs: ['Start'], gameplayContext: 'System' },
		{ actionId: 'back', label: 'Back', inputs: ['Back'], gameplayContext: 'System' },
		{ actionId: 'dpad', label: 'Directional Pad', inputs: ['DPadUp', 'DPadDown', 'DPadLeft', 'DPadRight'], gameplayContext: 'UI' },
		{ actionId: 'right_bumper', label: 'Right Bumper', inputs: ['RB'], gameplayContext: 'Modifier' },
	],
};

export function buildBangoProfile(playnowManifest: string, tutorialSpec: string): HybridGameProfile {
	return {
		gameId: 'bango-patoot',
		label: 'Bango-Patoot',
		renderMode: 'full3d-pseudo3d-hybrid',
		playnowManifest,
		tutorialSpec,
		controllerProfileId: bangoControllerProfile.profileId,
		supports: [
			'3DS runtime target',
			'Windows preview target',
			'idTech2 module target',
			'PlayNOW tutorial staging',
		],
	};
}

export function buildGenericProfile(): HybridGameProfile {
	return {
		gameId: 'generic-hybrid-game',
		label: 'Generic Hybrid Game Template',
		renderMode: 'full3d-pseudo3d-hybrid',
		controllerProfileId: bangoControllerProfile.profileId,
		supports: [
			'recursive pseudo-3D spaces',
			'full-3D proxy actors',
			'manifest-driven content ingest',
			'deterministic simulation',
		],
	};
}

export function buildDefaultDodoHybridRuntime(playnowManifest: string, tutorialSpec: string): HybridEngineRuntimeProfile {
	return {
		runtimeId: 'dodogame-orb-do-hybrid',
		label: 'DODOGame ORB/Do Hybrid Runtime',
		rendererPhilosophy: 'Use ORBEngine for recursive pseudo-3D presentation and DoENGINE for orchestration, input, telemetry, and shell state.',
		rendererBackend: shaderProgram.backend,
		renderStages,
		controllerProfiles: [bangoControllerProfile],
		games: [buildBangoProfile(playnowManifest, tutorialSpec), buildGenericProfile()],
		shaderProgram,
	};
}
