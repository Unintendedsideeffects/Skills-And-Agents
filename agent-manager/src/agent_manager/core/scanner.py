"""Filesystem scanner for finding agents and skills."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from agent_manager.core.parser import FrontmatterParser
from agent_manager.models import Agent, AgentMetadata, Skill, SkillMetadata


# Directories to skip during scanning
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
}


@dataclass
class ScanResult:
    """Result of scanning a directory tree."""

    agents: list[Agent] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)


class AgentSkillScanner:
    """
    Scans directory trees for agents and skills.

    Looks for:
    - .claude/agents/*.md (project-embedded agents)
    - agents/*.md (standalone agent repos)
    - .claude/skills/*/SKILL.md (project-embedded skills)
    - skills/*/SKILL.md (standalone skill repos)
    """

    def __init__(self):
        self.parser = FrontmatterParser()

    async def scan_path(self, root: Path) -> ScanResult:
        """
        Scan a single root path for agents and skills.

        Args:
            root: Root directory to scan

        Returns:
            ScanResult with discovered agents and skills
        """
        result = ScanResult()

        if not root.exists():
            result.errors.append((root, "Path does not exist"))
            return result

        if not root.is_dir():
            result.errors.append((root, "Path is not a directory"))
            return result

        # Run blocking I/O in thread pool
        await asyncio.to_thread(self._scan_recursive, root, root, result)
        return result

    async def scan_all(self, paths: list[Path]) -> ScanResult:
        """
        Scan multiple paths concurrently.

        Args:
            paths: List of root directories to scan

        Returns:
            Combined ScanResult from all paths
        """
        tasks = [self.scan_path(p) for p in paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined = ScanResult()
        for r in results:
            if isinstance(r, Exception):
                combined.errors.append((Path("."), str(r)))
            else:
                combined.agents.extend(r.agents)
                combined.skills.extend(r.skills)
                combined.errors.extend(r.errors)

        return combined

    def _scan_recursive(self, root: Path, current: Path, result: ScanResult) -> None:
        """Recursively scan directories for agents and skills."""
        try:
            for entry in current.iterdir():
                if entry.is_dir():
                    # Skip excluded directories
                    if entry.name in SKIP_DIRS:
                        continue

                    # Check for .claude directory
                    if entry.name == ".claude":
                        self._scan_claude_dir(root, entry, result)
                    # Check for standalone agents directory
                    elif entry.name == "agents":
                        self._scan_agents_dir(root, entry, result)
                    # Check for standalone skills directory
                    elif entry.name == "skills":
                        self._scan_skills_dir(root, entry, result)
                    else:
                        # Recurse into subdirectory
                        self._scan_recursive(root, entry, result)
        except PermissionError:
            result.errors.append((current, "Permission denied"))
        except OSError as e:
            result.errors.append((current, str(e)))

    def _scan_claude_dir(self, root: Path, claude_dir: Path, result: ScanResult) -> None:
        """Scan a .claude directory for agents and skills."""
        agents_dir = claude_dir / "agents"
        if agents_dir.exists() and agents_dir.is_dir():
            self._scan_agents_dir(root, agents_dir, result)

        skills_dir = claude_dir / "skills"
        if skills_dir.exists() and skills_dir.is_dir():
            self._scan_skills_dir(root, skills_dir, result)

    def _scan_agents_dir(self, root: Path, agents_dir: Path, result: ScanResult) -> None:
        """Scan an agents directory for .md files."""
        try:
            for entry in agents_dir.iterdir():
                if entry.is_file() and entry.suffix == ".md":
                    agent = self._parse_agent(entry, root)
                    if agent:
                        result.agents.append(agent)
        except OSError as e:
            result.errors.append((agents_dir, str(e)))

    def _scan_skills_dir(self, root: Path, skills_dir: Path, result: ScanResult) -> None:
        """Scan a skills directory for SKILL.md files."""
        try:
            for entry in skills_dir.iterdir():
                if entry.is_dir():
                    skill_file = entry / "SKILL.md"
                    if skill_file.exists():
                        skill = self._parse_skill(skill_file, entry, root)
                        if skill:
                            result.skills.append(skill)
        except OSError as e:
            result.errors.append((skills_dir, str(e)))

    def _parse_agent(self, file_path: Path, repo_root: Path) -> Agent | None:
        """Parse an agent file and return Agent object."""
        try:
            frontmatter, body = self.parser.parse(file_path)

            metadata = AgentMetadata(
                name=frontmatter.get("name", file_path.stem),
                description=frontmatter.get("description", ""),
                model=frontmatter.get("model", "sonnet"),
                color=frontmatter.get("color", "blue"),
                tags=frontmatter.get("tags", []),
                version=frontmatter.get("version"),
                author=frontmatter.get("author"),
                tools=frontmatter.get("tools", []),
            )

            return Agent(
                metadata=metadata,
                prompt=body,
                source_path=file_path.resolve(),
                source_repo=repo_root.resolve(),
            )
        except (ValueError, KeyError) as e:
            return None

    def _parse_skill(
        self, skill_file: Path, skill_dir: Path, repo_root: Path
    ) -> Skill | None:
        """Parse a skill file and return Skill object."""
        try:
            frontmatter, body = self.parser.parse(skill_file)

            metadata = SkillMetadata(
                name=frontmatter.get("name", skill_dir.name),
                description=frontmatter.get("description", ""),
            )

            # Find script files in skill directory
            scripts = []
            scripts_dir = skill_dir / "scripts"
            if scripts_dir.exists():
                scripts = list(scripts_dir.glob("*"))

            return Skill(
                metadata=metadata,
                content=body,
                source_path=skill_file.resolve(),
                source_dir=skill_dir.resolve(),
                source_repo=repo_root.resolve(),
                scripts=scripts,
            )
        except (ValueError, KeyError) as e:
            return None
