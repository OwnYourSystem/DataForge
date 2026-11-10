"""Read lessons from the curriculum directory."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from . import config


@dataclass(frozen=True)
class Lesson:
    id: str
    version: int
    title: str
    manifest: dict
    root: Path

    @property
    def editable_files(self) -> list[str]:
        return list(self.manifest["editable_files"])

    @property
    def operation_ids(self) -> list[str]:
        return [op["id"] for op in self.manifest["operations"]]

    @property
    def project_dir(self) -> Path:
        """Trusted dbt project files. The learner cannot change these."""
        return self.root / "project"

    def instructions(self) -> str:
        return (self.root / "instructions.md").read_text()

    def starter_files(self) -> dict[str, str]:
        return {p: (self.root / "starter" / p).read_text() for p in self.editable_files}


def load_lessons(root: Path | None = None) -> dict[str, Lesson]:
    root = root or config.curriculum_dir()
    lessons: dict[str, Lesson] = {}
    for manifest_path in sorted(root.glob("*/*/lesson.yaml")):
        manifest = yaml.safe_load(manifest_path.read_text())
        lesson = Lesson(
            id=manifest["id"],
            version=manifest["version"],
            title=manifest["title"],
            manifest=manifest,
            root=manifest_path.parent,
        )
        if lesson.id in lessons:
            raise ValueError(f"duplicate lesson id: {lesson.id}")
        lessons[lesson.id] = lesson
    return lessons
