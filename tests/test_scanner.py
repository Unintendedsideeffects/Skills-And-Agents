"""Tests for filesystem scanner."""

import pytest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_manager.core.scanner import AgentSkillScanner


@pytest.fixture
def scanner():
    """Create a scanner instance."""
    return AgentSkillScanner()


@pytest.fixture
def temp_project():
    """Create a temporary project structure."""
    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create agents directory
        agents_dir = base / "agents"
        agents_dir.mkdir()

        # Create a simple agent
        agent_file = agents_dir / "test-agent.md"
        agent_file.write_text("""---
name: test-agent
description: A test agent for testing purposes
model: sonnet
color: blue
---

This is a test agent system prompt.""")

        # Create .claude/agents directory
        claude_agents = base / ".claude" / "agents"
        claude_agents.mkdir(parents=True)

        claude_agent = claude_agents / "another-agent.md"
        claude_agent.write_text("""---
name: another-agent
description: Another test agent in .claude directory
model: opus
color: purple
---

This is another agent.""")

        # Create .claude/skills directory
        claude_skills = base / ".claude" / "skills"
        claude_skills.mkdir(parents=True)

        skill_dir = claude_skills / "test-skill"
        skill_dir.mkdir()

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill
---

This is a test skill.""")

        yield base


@pytest.mark.asyncio
async def test_scan_finds_agents(scanner, temp_project):
    """Test that scanner finds agents."""
    result = await scanner.scan_path(temp_project)

    assert len(result.agents) == 2
    agent_names = {a.metadata.name for a in result.agents}
    assert "test-agent" in agent_names
    assert "another-agent" in agent_names


@pytest.mark.asyncio
async def test_scan_finds_skills(scanner, temp_project):
    """Test that scanner finds skills."""
    result = await scanner.scan_path(temp_project)

    assert len(result.skills) == 1
    assert result.skills[0].metadata.name == "test-skill"


@pytest.mark.asyncio
async def test_scan_nonexistent_path(scanner):
    """Test scanning nonexistent path."""
    result = await scanner.scan_path(Path("/nonexistent/path"))

    assert len(result.agents) == 0
    assert len(result.skills) == 0
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_scan_all(scanner, temp_project):
    """Test scanning multiple paths."""
    result = await scanner.scan_all([temp_project, Path("/nonexistent")])

    assert len(result.agents) == 2
    assert len(result.skills) == 1
    assert len(result.errors) == 1  # The nonexistent path
