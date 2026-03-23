import argparse
import json
import struct
from pathlib import Path


MAGIC = 0x4D534652
VERSION = 4


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    def take(self, size: int) -> bytes:
        chunk = self.data[self.offset:self.offset + size]
        if len(chunk) != size:
            raise ValueError("Unexpected end of file")
        self.offset += size
        return chunk

    def u32(self) -> int:
        return struct.unpack("<I", self.take(4))[0]

    def u64(self) -> int:
        return struct.unpack("<Q", self.take(8))[0]

    def f64(self) -> float:
        return struct.unpack("<d", self.take(8))[0]

    def text(self) -> str:
        length = self.u32()
        return self.take(length).decode("utf-8")


def read_agent(reader: Reader) -> dict:
    agent = {
        "name": reader.text(),
        "id_weight": reader.f64(),
        "ego_weight": reader.f64(),
        "superego_weight": reader.f64(),
        "pattern_trust": reader.f64(),
        "bias_action": [reader.f64() for _ in range(3)],
    }
    memory_count = reader.u64()
    memory = []
    for _ in range(memory_count):
        memory.append(
            {
                "action": reader.u32(),
                "reward": reader.f64(),
                "context": reader.u32(),
            }
        )
    agent["memory_count"] = memory_count
    agent["memory"] = memory
    return agent


def read_replay(reader: Reader) -> dict:
    capacity = reader.u64()
    count = reader.u64()
    next_index = reader.u64()
    replay = {
        "capacity": capacity,
        "count": count,
        "next_index": next_index,
        "total_priority": reader.f64(),
        "decay": reader.f64(),
        "tick": reader.u64(),
        "entries": [],
    }
    for _ in range(count):
        replay["entries"].append(
            {
                "state": reader.u32(),
                "action": reader.u32(),
                "reward": reader.f64(),
                "next_state": reader.u32(),
                "done": reader.u32(),
                "priority": reader.f64(),
                "timestamp": reader.u64(),
            }
        )
    return replay


def read_planner(reader: Reader) -> dict:
    states = reader.u32()
    actions = reader.u32()
    alpha = reader.f64()
    gamma = reader.f64()
    epsilon = reader.f64()
    q_values = [reader.f64() for _ in range(states * actions)]
    return {
        "states": states,
        "actions": actions,
        "alpha": alpha,
        "gamma": gamma,
        "epsilon": epsilon,
        "q_values": q_values,
    }


def read_tactics(reader: Reader) -> dict:
    slots = 8
    tactics = {
        "action_uses": [reader.u64() for _ in range(slots)],
        "action_successes": [reader.u64() for _ in range(slots)],
        "action_failures": [reader.u64() for _ in range(slots)],
        "combo_links": [],
    }
    for _ in range(slots):
        tactics["combo_links"].append([reader.u64() for _ in range(slots)])
    tactics["last_action"] = reader.u32() - 1
    tactics["combo_commitment"] = reader.f64()
    tactics["pressure_bias"] = reader.f64()
    tactics["counter_bias"] = reader.f64()
    tactics["spacing_bias"] = reader.f64()
    return tactics


def read_morals(reader: Reader) -> dict:
    return {
        "mercy": reader.f64(),
        "duty": reader.f64(),
        "candor": reader.f64(),
        "ambition": reader.f64(),
        "dialogue_choices": reader.u64(),
        "spared_count": reader.u64(),
        "punished_count": reader.u64(),
        "promises_kept": reader.u64(),
        "promises_broken": reader.u64(),
    }


def read_genome(reader: Reader) -> dict:
    return {
        "personality": [reader.f64() for _ in range(6)],
        "intellect": [reader.f64() for _ in range(6)],
        "ethics": [reader.f64() for _ in range(6)],
    }


def read_consciousness(reader: Reader) -> dict:
    return {
        "unconscious_pull": reader.f64(),
        "subconscious_pull": reader.f64(),
        "conscious_pull": reader.f64(),
        "peripheral_awareness": reader.f64(),
        "discovery_drive": reader.f64(),
        "frequency": [reader.f64() for _ in range(5)],
    }


def read_narrative_hooks(reader: Reader) -> dict:
    return {
        "active": reader.u32(),
        "revelation_pressure": reader.f64(),
        "alliance_pressure": reader.f64(),
        "rupture_pressure": reader.f64(),
        "ending_pressure": reader.f64(),
        "omen_pressure": reader.f64(),
    }


def read_actor_profile(reader: Reader) -> dict:
    return {
        "label": reader.text(),
        "genome": read_genome(reader),
        "consciousness": read_consciousness(reader),
        "narrative": read_narrative_hooks(reader),
    }


def read_resonance(reader: Reader) -> dict:
    return {
        "frequency": [reader.f64() for _ in range(5)],
        "familiarity": reader.f64(),
        "reciprocity": reader.f64(),
        "tension": reader.f64(),
        "permeability": reader.f64(),
    }


def threat_for(rival: dict) -> float:
    return (
        rival["grudge"] * 0.26
        + rival["dominance"] * 0.18
        + rival["adaptability"] * 0.14
        + min(rival["engagements"], 64) * 0.003
        + rival["survives"] * 0.02
        + rival["tactics"]["pressure_bias"] * 0.14
        + rival["tactics"]["combo_commitment"] * 0.10
        + rival["tactics"]["counter_bias"] * 0.08
        + rival["morals"]["ambition"] * 0.06
        + rival["morals"]["duty"] * 0.04
        + (1.0 - rival["morals"]["mercy"]) * 0.03
        - rival["fear"] * 0.10
    )


def inspect_save(path: Path, include_full: bool) -> dict:
    reader = Reader(path.read_bytes())
    magic = reader.u32()
    version = reader.u32()
    if magic != MAGIC:
        raise ValueError(f"Unexpected magic: {magic:#x}")
    if version not in (1, 2, 3, VERSION):
        raise ValueError(f"Unsupported version: {version}")

    count = reader.u64()
    capacity = reader.u64()
    tick = reader.u64()
    if version == 1:
        config = {
            "replay_capacity": 256,
            "replay_decay": 0.997,
            "planner_states": 16,
            "planner_actions": 3,
            "planner_alpha": 0.08,
            "planner_gamma": 0.92,
            "planner_epsilon": 0.18,
        }
    else:
        config = {
            "replay_capacity": reader.u64(),
            "replay_decay": reader.f64(),
            "planner_states": reader.u32(),
            "planner_actions": reader.u32(),
            "planner_alpha": reader.f64(),
            "planner_gamma": reader.f64(),
            "planner_epsilon": reader.f64(),
        }
        if version >= 4:
            config["narrative_protocol_enabled"] = reader.u32()

    player_model = None
    collective_field = None
    dormant_narrative = None
    if version >= 4:
        player_model = read_actor_profile(reader)
        collective_field = read_consciousness(reader)
        dormant_narrative = read_narrative_hooks(reader)

    rivals = []
    for _ in range(count):
        rival = {
            "id": reader.u32(),
            "name": reader.text(),
            "archetype": reader.text(),
            "grudge": reader.f64(),
            "fear": reader.f64(),
            "dominance": reader.f64(),
            "adaptability": reader.f64(),
            "engagements": reader.u64() if version >= 3 else reader.u32(),
            "defeats": reader.u32(),
            "survives": reader.u32(),
        }
        if version >= 3:
            rival["tactics"] = read_tactics(reader)
            rival["morals"] = read_morals(reader)
        else:
            rival["tactics"] = {
                "action_uses": [0] * 8,
                "action_successes": [0] * 8,
                "action_failures": [0] * 8,
                "combo_links": [[0] * 8 for _ in range(8)],
                "last_action": -1,
                "combo_commitment": 0.0,
                "pressure_bias": 0.0,
                "counter_bias": 0.0,
                "spacing_bias": 0.0,
            }
            rival["morals"] = {
                "mercy": 0.5,
                "duty": 0.5,
                "candor": 0.5,
                "ambition": 0.5,
                "dialogue_choices": 0,
                "spared_count": 0,
                "punished_count": 0,
                "promises_kept": 0,
                "promises_broken": 0,
            }
        if version >= 4:
            rival["self_model"] = read_actor_profile(reader)
            rival["player_resonance"] = read_resonance(reader)
        rival["psyche"] = read_agent(reader)
        rival["replay"] = read_replay(reader)
        rival["planner"] = read_planner(reader)
        rival["threat"] = round(threat_for(rival), 4)
        if not include_full:
            rival["psyche"].pop("memory", None)
            rival["replay"].pop("entries", None)
            rival["planner"].pop("q_values", None)
        rivals.append(rival)

    return {
        "path": str(path),
        "magic": hex(magic),
        "version": version,
        "count": count,
        "capacity": capacity,
        "tick": tick,
        "config": config,
        "player_model": player_model,
        "collective_field": collective_field,
        "dormant_narrative": dormant_narrative,
        "rivals": rivals,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect egosphere MindSphere save files.")
    parser.add_argument("path", type=Path, help="Path to a .dat save produced by mindsphere_save(...)")
    parser.add_argument("--full", action="store_true", help="Include full replay entries, agent memory, and planner Q values")
    args = parser.parse_args()

    report = inspect_save(args.path, include_full=args.full)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())