"""Skill data models."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agent_manager.models.agent import LinkScope


@dataclass
class SkillMetadata:
    """Parsed YAML frontmatter from SKILL.md."""

    name: str
    description: str


@dataclass
class Skill:
    """Complete skill representation."""

    metadata: SkillMetadata
    content: str
    source_path: Path
    source_dir: Path
    source_repo: Path
    scripts: list[Path] = field(default_factory=list)
    global_link: Optional[Path] = None
    project_links: list[Path] = field(default_factory=list)

    @property
    def dirname(self) -> str:
        """Get the skill directory name."""
        return self.source_dir.name

    @property
    def link_status(self) -> LinkScope:
        """Get current link status."""
        if self.global_link and self.global_link.exists():
            return LinkScope.GLOBAL
        elif self.project_links:
            return LinkScope.PROJECT
        return LinkScope.UNLINKED

    @property
    def display_name(self) -> str:
        """Get display name for UI."""
        return self.metadata.name.replace("-", " ").title()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "source_path": str(self.source_path),
            "source_dir": str(self.source_dir),
            "source_repo": str(self.source_repo),
            "scripts": [str(s) for s in self.scripts],
            "link_status": self.link_status.value,
        }
