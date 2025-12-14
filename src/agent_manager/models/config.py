"""Configuration data models."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ScanPath:
    """A configured scan location."""

    path: Path
    enabled: bool = True
    last_scanned: Optional[datetime] = None
    agent_count: int = 0
    skill_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "enabled": self.enabled,
            "last_scanned": self.last_scanned.isoformat() if self.last_scanned else None,
            "agent_count": self.agent_count,
            "skill_count": self.skill_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScanPath":
        """Create from dictionary."""
        return cls(
            path=Path(data["path"]),
            enabled=data.get("enabled", True),
            last_scanned=(
                datetime.fromisoformat(data["last_scanned"])
                if data.get("last_scanned")
                else None
            ),
            agent_count=data.get("agent_count", 0),
            skill_count=data.get("skill_count", 0),
        )


@dataclass
class ProjectAssignment:
    """Tracks agent/skill assignments to a project."""

    project_path: Path
    agent_names: list[str] = field(default_factory=list)
    skill_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "project_path": str(self.project_path),
            "agent_names": self.agent_names,
            "skill_names": self.skill_names,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectAssignment":
        """Create from dictionary."""
        return cls(
            project_path=Path(data["project_path"]),
            agent_names=data.get("agent_names", []),
            skill_names=data.get("skill_names", []),
        )


@dataclass
class AppConfig:
    """Application configuration."""

    scan_paths: list[ScanPath] = field(default_factory=list)
    global_agents: list[str] = field(default_factory=list)
    global_skills: list[str] = field(default_factory=list)
    project_assignments: list[ProjectAssignment] = field(default_factory=list)
    theme: str = "dark"
    vim_mode: bool = True
    show_preview: bool = True
    preview_width: int = 50

    @property
    def config_dir(self) -> Path:
        """Get config directory path."""
        return Path.home() / ".config" / "agent-manager"

    @property
    def claude_dir(self) -> Path:
        """Get Claude directory path."""
        return Path.home() / ".claude"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "scan_paths": [sp.to_dict() for sp in self.scan_paths],
            "global_agents": self.global_agents,
            "global_skills": self.global_skills,
            "project_assignments": [pa.to_dict() for pa in self.project_assignments],
            "theme": self.theme,
            "vim_mode": self.vim_mode,
            "show_preview": self.show_preview,
            "preview_width": self.preview_width,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """Create from dictionary."""
        return cls(
            scan_paths=[ScanPath.from_dict(sp) for sp in data.get("scan_paths", [])],
            global_agents=data.get("global_agents", []),
            global_skills=data.get("global_skills", []),
            project_assignments=[
                ProjectAssignment.from_dict(pa)
                for pa in data.get("project_assignments", [])
            ],
            theme=data.get("theme", "dark"),
            vim_mode=data.get("vim_mode", True),
            show_preview=data.get("show_preview", True),
            preview_width=data.get("preview_width", 50),
        )
