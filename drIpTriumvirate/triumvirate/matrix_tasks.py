"""Matrix-style task management for the video assembly pipeline."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum


class TaskState(str, Enum):
    INIT = "INIT"
    DRAFT = "DRAFT"
    FEEL = "FEEL"
    SIGNAL = "SIGNAL"
    RENDER = "RENDER"
    ENCODE = "ENCODE"
    REVIEW = "REVIEW"
    SUBMIT = "SUBMIT"
    LIVE = "LIVE"


_STATE_ORDER = list(TaskState)


@dataclass
class MatrixTask:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    label: str = ""
    state: TaskState = TaskState.INIT
    priority: int = 5
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = self.state.value
        return d


class TaskBoard:
    def __init__(self) -> None:
        self.tasks: list[MatrixTask] = []

    def add(self, label: str, priority: int = 5) -> MatrixTask:
        task = MatrixTask(label=label, priority=priority)
        self.tasks.append(task)
        return task

    def advance(self, task_id: str) -> MatrixTask | None:
        task = self._find(task_id)
        if task is None:
            return None
        idx = _STATE_ORDER.index(task.state)
        if idx < len(_STATE_ORDER) - 1:
            task.state = _STATE_ORDER[idx + 1]
            task.updated = time.time()
        return task

    def remove(self, task_id: str) -> bool:
        task = self._find(task_id)
        if task:
            self.tasks.remove(task)
            return True
        return False

    def attach_artifact(self, task_id: str, artifact: str) -> "MatrixTask | None":
        """Attach an artifact label (e.g. a generated file path) to a task."""
        task = self._find(task_id)
        if task:
            task.artifacts.append(artifact[:200])
            task.updated = time.time()
        return task

    def _find(self, task_id: str) -> MatrixTask | None:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def to_dict(self) -> dict:
        return {
            "tasks": [t.to_dict() for t in sorted(self.tasks, key=lambda t: (-t.priority, t.created))],
            "total": len(self.tasks),
            "states": {
                state.value: sum(1 for t in self.tasks if t.state == state)
                for state in TaskState
            },
        }

    def terminal_view(self) -> list[str]:
        """Generate ls -la style terminal output."""
        lines = [
            f"total {len(self.tasks)}",
            "STATE     PRI  ID        ARTIFACT                          LABEL",
            "--------  ---  --------  --------------------------------  ----------------------------",
        ]
        for task in sorted(self.tasks, key=lambda t: (-t.priority, t.created)):
            artifact = task.artifacts[-1] if task.artifacts else "---"
            if len(artifact) > 32:
                artifact = artifact[:29] + "..."
            lines.append(f"{task.state.value:<9} {task.priority:>3}  {task.id:<8}  {artifact:<32}  {task.label}")
        return lines
