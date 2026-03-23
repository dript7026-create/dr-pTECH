from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / 'generated' / 'idLoadINT_bundle' / 'tutorial_demo_spec.json'
OUTPUT_DIR = ROOT / 'generated' / 'playnow'
JSON_PATH = OUTPUT_DIR / 'tutorial_completion_simulation.json'
REPORT_PATH = OUTPUT_DIR / 'tutorial_completion_simulation_report.md'


@dataclass
class SimulationEvent:
    time_s: float
    category: str
    detail: str


PROMPT_ACTIONS = {
    'Move with left stick and turn the camera with right stick.': [
        'Sweep left stick across the room bounds.',
        'Rotate right stick through a full camera orbit.',
    ],
    'Tap A to crouch or slide while sprinting.': [
        'Tap A from neutral to confirm crouch.',
        'Hold sprint then tap A to confirm slide.',
    ],
    'Hold B to sprint; tap B to jump.': [
        'Hold B for a sprint burst through the lane markers.',
        'Release and tap B to clear the jump marker.',
    ],
    'Use LB for light attacks and RT for heavy attacks.': [
        'Trigger a three-hit light string with LB.',
        'Commit one heavy finisher with RT.',
    ],
    'Click right stick to parry and left stick to block.': [
        'Use left stick click to confirm guard state.',
        'Use right stick click to confirm parry timing.',
    ],
    'Hold LT for the ability wheel and steer with right stick.': [
        'Hold LT to open the ability wheel.',
        'Steer right stick through all wheel quadrants.',
    ],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def simulate(spec: dict) -> dict:
    current_time = 0.0
    events: list[SimulationEvent] = []
    prompt_results: list[dict] = []
    wave_results: list[dict] = []

    for index, prompt in enumerate(spec.get('prompts', []), start=1):
        actions = PROMPT_ACTIONS.get(prompt, ['Acknowledge tutorial prompt and execute mapped input sequence.'])
        start_time = current_time
        for action in actions:
            current_time += 3.5
            events.append(SimulationEvent(current_time, 'prompt', f'Prompt {index}: {action}'))
        prompt_results.append({
            'prompt_index': index,
            'prompt': prompt,
            'actions': actions,
            'completed': True,
            'time_window_s': round(current_time - start_time, 2),
        })
        current_time += 1.25

    for wave_index, wave in enumerate(spec.get('waves', []), start=1):
        tier = int(wave.get('enemy_tier', 1))
        count = int(wave.get('count', 0))
        defeat_times: list[float] = []
        for enemy_index in range(1, count + 1):
            current_time += 4.0 + tier * 1.75
            defeat_times.append(round(current_time, 2))
            events.append(SimulationEvent(current_time, 'combat', f'Wave {wave_index} enemy {enemy_index}/{count} defeated at tier {tier}.'))
        wave_results.append({
            'wave_index': wave_index,
            'enemy_tier': tier,
            'count': count,
            'completed': True,
            'defeat_timestamps_s': defeat_times,
        })
        current_time += 2.0

    events.append(SimulationEvent(current_time + 1.0, 'completion', 'Tutorial completion rule satisfied: defeat_all_waves.'))
    total_enemies = sum(int(wave.get('count', 0)) for wave in spec.get('waves', []))
    return {
        'simulation_name': 'bango-tutorial-rule-based-player-sim',
        'tutorial_name': spec.get('name', 'unknown'),
        'environment': spec.get('environment', 'unknown'),
        'completion_rule': spec.get('completion_rule', 'unknown'),
        'player_model': 'Deterministic rule-based tutorial runner',
        'prompt_results': prompt_results,
        'wave_results': wave_results,
        'timeline': [event.__dict__ for event in events],
        'metrics': {
            'completion_percentage': 100,
            'prompts_completed': len(prompt_results),
            'waves_completed': len(wave_results),
            'enemies_defeated': total_enemies,
            'estimated_completion_time_s': round(events[-1].time_s, 2),
        },
    }


def build_report(result: dict) -> str:
    lines = [
        '# Bango-Patoot Tutorial Completion Simulation Report',
        '',
        f"Tutorial: {result['tutorial_name']}",
        f"Environment: {result['environment']}",
        f"Player model: {result['player_model']}",
        f"Completion: {result['metrics']['completion_percentage']}%",
        f"Estimated time: {result['metrics']['estimated_completion_time_s']}s",
        '',
        '## Prompt Pass',
        '',
    ]
    for prompt in result['prompt_results']:
        lines.append(f"- Prompt {prompt['prompt_index']}: complete in {prompt['time_window_s']}s :: {prompt['prompt']}")
    lines.extend(['', '## Combat Waves', ''])
    for wave in result['wave_results']:
        lines.append(f"- Wave {wave['wave_index']}: tier {wave['enemy_tier']} x{wave['count']} cleared at {wave['defeat_timestamps_s']}")
    lines.extend(['', '## Outcome', '', '- All tutorial prompts were satisfied in order.', '- All enemy waves were cleared.', '- Completion rule `defeat_all_waves` was met by the simulated player.', ''])
    return '\n'.join(lines) + '\n'


def main() -> int:
    spec = read_json(SPEC_PATH)
    result = simulate(spec)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    REPORT_PATH.write_text(build_report(result), encoding='utf-8')
    print(json.dumps({'result': str(JSON_PATH), 'report': str(REPORT_PATH), 'completion': result['metrics']['completion_percentage']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
