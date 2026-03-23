import { DoNowRuntimeEntry, DoNowRuntimeManifest, PipelineAssetRecord } from '../../shared/src/contracts';

function classifyRuntimeBucket(category: string): string {
    switch (category) {
        case 'character_sheet':
            return 'actors';
        case 'animation_pack':
            return 'animation_streams';
        case 'environment_set':
            return 'world_tiles';
        case 'hud_pack':
            return 'ui';
        case 'combat_fx':
        case 'environmental_fx':
            return 'effects';
        case 'armor_set':
        case 'weapon_pack':
        case 'item_pack':
        case 'ammunition_pack':
            return 'equipment';
        case 'animated_environment_object':
        case 'apiary_sheet':
            return 'interactive_world';
        default:
            return 'support';
    }
}

export function buildDoNowEntry(asset: PipelineAssetRecord): DoNowRuntimeEntry {
    return {
        assetId: asset.assetId,
        category: asset.category,
        runtimeBucket: classifyRuntimeBucket(asset.category),
        sourcePath: asset.sourcePath,
        immediateReady: true,
        generatedOutputs: asset.derivedOutputs ?? [],
    };
}

export function buildDoNowManifest(projectName: string, assets: PipelineAssetRecord[]): DoNowRuntimeManifest {
    const entries = assets.map(buildDoNowEntry);
    const preloadGroups = [
        { name: 'hero_bootstrap', matchBuckets: ['actors', 'animation_streams', 'ui'] },
        { name: 'world_bootstrap', matchBuckets: ['world_tiles', 'interactive_world', 'effects'] },
        { name: 'equipment_bootstrap', matchBuckets: ['equipment', 'support'] },
    ];

    return {
        projectName,
        streamName: `${projectName}_clip_blend_id_stream`,
        immediateFunctionality: [
            'mount primary actor packages',
            'bind core HUD and interaction states',
            'preload world tile and FX bundles',
            'activate animation and equipment registries',
        ],
        preloadGroups,
        entries,
    };
}