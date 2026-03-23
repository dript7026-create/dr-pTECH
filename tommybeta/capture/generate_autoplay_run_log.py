from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from tests.test_tommybeta_completion import SPECIALS, TommyBetaRunSim


OUT_JSON = ROOT / "capture" / "tommybeta_100_percent_run_log.json"
OUT_TXT = ROOT / "capture" / "tommybeta_100_percent_run_log.txt"


class ReportingSim(TommyBetaRunSim):
    def __init__(self):
        super().__init__()
        self.fight_log = []

    def between_choice(self):
        self.history_cunning += 1
        self.add_xp(14)
        return "CUNNING"

    def run_to_completion(self):
        fights = 0
        while self.finisher_mask != 0xFF:
            target_special = self.choose_target_special()
            before_frame = self.frame
            won = self.run_fight(target_special)
            fights += 1
            entry = {
                "won": won,
                "target_special": target_special,
                "target_special_name": SPECIALS[target_special][0],
                "combat_frames": self.frame - before_frame,
                "tommy_health": self.tommy.health,
                "level": self.level,
                "mask": self.finisher_mask,
                "fight": fights,
            }
            if not won:
                self.fight_log.append(entry)
                return {
                    "won": False,
                    "fights": fights,
                    "level": self.level,
                    "mask": self.finisher_mask,
                    "fight_log": self.fight_log,
                }
            if self.finisher_mask != 0xFF:
                entry["history_pick"] = self.between_choice()
            else:
                entry["history_pick"] = None
            self.fight_log.append(entry)
        return {
            "won": True,
            "fights": fights,
            "level": self.level,
            "mask": self.finisher_mask,
            "xp": self.xp,
            "unlocked_specials": self.unlocked_specials,
            "history": (self.history_hunt, self.history_cunning, self.history_endure),
            "fight_log": self.fight_log,
        }


def main() -> None:
    sim = ReportingSim()
    result = sim.run_to_completion()
    combat_frames = sum(entry["combat_frames"] for entry in result["fight_log"])
    estimated_runtime_seconds = combat_frames / 59.94 + 73.0

    payload = {
        **result,
        "combat_frames": combat_frames,
        "estimated_runtime_seconds": round(estimated_runtime_seconds, 2),
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "TommyBeta 100% Autoplay Run Log",
        "",
        f"won: {payload['won']}",
        f"fights: {payload['fights']}",
        f"level: {payload['level']}",
        f"xp: {payload.get('xp', 0)}",
        f"finisher_mask: 0x{payload['mask']:02X}",
        f"unlocked_specials: {payload.get('unlocked_specials', 0)}",
        f"history: hunt={payload.get('history', (0, 0, 0))[0]}, cunning={payload.get('history', (0, 0, 0))[1]}, endure={payload.get('history', (0, 0, 0))[2]}",
        f"combat_frames: {combat_frames}",
        f"estimated_runtime_seconds: {payload['estimated_runtime_seconds']}",
        "",
        "Fight log:",
    ]
    for entry in payload["fight_log"]:
        history_pick = entry["history_pick"] if entry["history_pick"] is not None else "-"
        lines.append(
            f"fight {entry['fight']}: target_special={entry['target_special_name']} won={entry['won']} level={entry['level']} "
            f"finisher_mask=0x{entry['mask']:02X} combat_frames={entry['combat_frames']} history_pick={history_pick}"
        )
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()