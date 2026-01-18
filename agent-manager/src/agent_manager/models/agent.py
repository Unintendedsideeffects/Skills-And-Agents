"""Agent data models."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class LinkScope(Enum):
    """Symlink scope for an agent."""

    UNLINKED = "unlinked"
    GLOBAL = "global"
    PROJECT = "project"


@dataclass
class AgentMetadata:
    """Parsed YAML frontmatter from agent markdown file."""

    name: str
    description: str
    model: str
    color: str = "blue"
    tags: list[str] = field(default_factory=list)
    version: Optional[str] = None
    author: Optional[str] = None
    tools: list[str] = field(default_factory=list)


@dataclass
class Agent:
    """Complete agent representation."""

    metadata: AgentMetadata
    prompt: str
    source_path: Path
    source_repo: Path
    global_link: Optional[Path] = None
    project_links: list[Path] = field(default_factory=list)

    @property
    def filename(self) -> str:
        """Get the agent filename."""
        return self.source_path.name

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
            "model": self.metadata.model,
            "color": self.metadata.color,
            "tags": self.metadata.tags,
            "version": self.metadata.version,
            "author": self.metadata.author,
            "tools": self.metadata.tools,
            "source_path": str(self.source_path),
            "source_repo": str(self.source_repo),
            "link_status": self.link_status.value,
        }
