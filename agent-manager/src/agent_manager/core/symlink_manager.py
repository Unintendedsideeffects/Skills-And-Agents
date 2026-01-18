"""Symlink management for agents and skills."""

from enum import Enum
from pathlib import Path


class LinkResult(Enum):
    """Result of a symlink operation."""

    SUCCESS = "success"
    ALREADY_EXISTS = "already_exists"
    CONFLICT = "conflict"
    TARGET_MISSING = "target_missing"
    PERMISSION_DENIED = "permission_denied"
    ERROR = "error"


class SymlinkManager:
    """
    Manages symlinks for agents and skills.

    Target Locations:
    - Global: ~/.claude/agents/ and ~/.claude/skills/
    - Project: /path/to/project/.claude/agents/ and .claude/skills/
    """

    def __init__(self, claude_dir: Path | None = None):
        """
        Initialize the symlink manager.

        Args:
            claude_dir: Override Claude directory (default: ~/.claude)
        """
        self.claude_dir = claude_dir or (Path.home() / ".claude")
        self.global_agents_dir = self.claude_dir / "agents"
        self.global_skills_dir = self.claude_dir / "skills"

    # Agent operations
    def link_agent_global(self, source: Path) -> LinkResult:
        """
        Create symlink for agent in ~/.claude/agents/.

        Args:
            source: Path to the agent .md file

        Returns:
            LinkResult indicating success or failure reason
        """
        target = self.global_agents_dir / source.name
        return self._create_symlink(source, target)

    def link_agent_to_project(self, source: Path, project: Path) -> LinkResult:
        """
        Create symlink for agent in project's .claude/agents/.

        Args:
            source: Path to the agent .md file
            project: Root path of the project

        Returns:
            LinkResult indicating success or failure reason
        """
        target = project / ".claude" / "agents" / source.name
        return self._create_symlink(source, target)

    def unlink_agent_global(self, agent_name: str) -> bool:
        """
        Remove global symlink for agent.

        Args:
            agent_name: Filename of the agent (e.g., "my-agent.md")

        Returns:
            True if removed, False otherwise
        """
        if not agent_name.endswith(".md"):
            agent_name = f"{agent_name}.md"
        target = self.global_agents_dir / agent_name
        return self._remove_symlink(target)

    def unlink_agent_from_project(self, agent_name: str, project: Path) -> bool:
        """
        Remove project symlink for agent.

        Args:
            agent_name: Filename of the agent
            project: Root path of the project

        Returns:
            True if removed, False otherwise
        """
        if not agent_name.endswith(".md"):
            agent_name = f"{agent_name}.md"
        target = project / ".claude" / "agents" / agent_name
        return self._remove_symlink(target)

    # Skill operations
    def link_skill_global(self, source_dir: Path) -> LinkResult:
        """
        Create symlink for skill directory in ~/.claude/skills/.

        Args:
            source_dir: Path to the skill directory

        Returns:
            LinkResult indicating success or failure reason
        """
        target = self.global_skills_dir / source_dir.name
        return self._create_symlink(source_dir, target)

    def link_skill_to_project(self, source_dir: Path, project: Path) -> LinkResult:
        """
        Create symlink for skill directory in project's .claude/skills/.

        Args:
            source_dir: Path to the skill directory
            project: Root path of the project

        Returns:
            LinkResult indicating success or failure reason
        """
        target = project / ".claude" / "skills" / source_dir.name
        return self._create_symlink(source_dir, target)

    def unlink_skill_global(self, skill_name: str) -> bool:
        """
        Remove global symlink for skill.

        Args:
            skill_name: Directory name of the skill

        Returns:
            True if removed, False otherwise
        """
        target = self.global_skills_dir / skill_name
        return self._remove_symlink(target)

    def unlink_skill_from_project(self, skill_name: str, project: Path) -> bool:
        """
        Remove project symlink for skill.

        Args:
            skill_name: Directory name of the skill
            project: Root path of the project

        Returns:
            True if removed, False otherwise
        """
        target = project / ".claude" / "skills" / skill_name
        return self._remove_symlink(target)

    # Status checking
    def get_agent_link_status(self, source: Path) -> dict:
        """
        Check where an agent is currently linked.

        Args:
            source: Path to the agent .md file

        Returns:
            Dict with global_linked, global_target, and project_links
        """
        global_target = self.global_agents_dir / source.name
        global_linked = (
            global_target.is_symlink()
            and global_target.resolve() == source.resolve()
        )

        return {
            "global_linked": global_linked,
            "global_target": global_target if global_linked else None,
            "project_links": [],  # TODO: Track project links
        }

    def get_skill_link_status(self, source_dir: Path) -> dict:
        """
        Check where a skill is currently linked.

        Args:
            source_dir: Path to the skill directory

        Returns:
            Dict with global_linked, global_target, and project_links
        """
        global_target = self.global_skills_dir / source_dir.name
        global_linked = (
            global_target.is_symlink()
            and global_target.resolve() == source_dir.resolve()
        )

        return {
            "global_linked": global_linked,
            "global_target": global_target if global_linked else None,
            "project_links": [],
        }

    # Private helpers
    def _create_symlink(self, source: Path, target: Path) -> LinkResult:
        """
        Create a symlink with proper error handling.

        Args:
            source: Source path (file or directory)
            target: Target path for the symlink

        Returns:
            LinkResult indicating outcome
        """
        if not source.exists():
            return LinkResult.TARGET_MISSING

        # Ensure parent directory exists
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            return LinkResult.PERMISSION_DENIED
        except OSError:
            return LinkResult.ERROR

        # Check if target already exists
        if target.is_symlink():
            if target.resolve() == source.resolve():
                return LinkResult.ALREADY_EXISTS
            # Different source - conflict
            return LinkResult.CONFLICT
        elif target.exists():
            # Regular file/dir exists - conflict
            return LinkResult.CONFLICT

        # Create symlink
        try:
            target.symlink_to(source)
            return LinkResult.SUCCESS
        except PermissionError:
            return LinkResult.PERMISSION_DENIED
        except OSError:
            return LinkResult.ERROR

    def _remove_symlink(self, target: Path) -> bool:
        """
        Remove a symlink if it exists.

        Args:
            target: Path to the symlink

        Returns:
            True if removed, False otherwise
        """
        if target.is_symlink():
            try:
                target.unlink()
                return True
            except (PermissionError, OSError):
                return False
        return False
