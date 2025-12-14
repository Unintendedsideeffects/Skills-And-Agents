"""Tests for symlink manager."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_manager.core.symlink_manager import SymlinkManager, LinkResult


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        source_dir = base / "sources"
        source_dir.mkdir()

        # Create test agent file
        agent_file = source_dir / "test-agent.md"
        agent_file.write_text("# Test Agent\n\nContent")

        # Create Claude dir
        claude_dir = base / ".claude"
        claude_dir.mkdir()

        yield agent_file, claude_dir


def test_link_agent_global_success(temp_dirs):
    """Test successful global linking."""
    agent_file, claude_dir = temp_dirs
    manager = SymlinkManager(claude_dir=claude_dir)

    result = manager.link_agent_global(agent_file)
    assert result == LinkResult.SUCCESS

    # Check symlink was created
    target = claude_dir / "agents" / agent_file.name
    assert target.is_symlink()
    assert target.resolve() == agent_file.resolve()


def test_link_agent_global_already_linked(temp_dirs):
    """Test linking already linked agent."""
    agent_file, claude_dir = temp_dirs
    manager = SymlinkManager(claude_dir=claude_dir)

    # Link once
    result1 = manager.link_agent_global(agent_file)
    assert result1 == LinkResult.SUCCESS

    # Try to link again
    result2 = manager.link_agent_global(agent_file)
    assert result2 == LinkResult.ALREADY_EXISTS


def test_link_agent_global_missing_source(temp_dirs):
    """Test linking with missing source."""
    _, claude_dir = temp_dirs
    manager = SymlinkManager(claude_dir=claude_dir)

    nonexistent = Path("/nonexistent/agent.md")
    result = manager.link_agent_global(nonexistent)
    assert result == LinkResult.TARGET_MISSING


def test_unlink_agent(temp_dirs):
    """Test unlinking an agent."""
    agent_file, claude_dir = temp_dirs
    manager = SymlinkManager(claude_dir=claude_dir)

    # Link first
    manager.link_agent_global(agent_file)

    # Then unlink
    success = manager.unlink_agent_global(agent_file.name)
    assert success

    target = claude_dir / "agents" / agent_file.name
    assert not target.exists()


def test_unlink_nonexistent(temp_dirs):
    """Test unlinking that doesn't exist."""
    _, claude_dir = temp_dirs
    manager = SymlinkManager(claude_dir=claude_dir)

    success = manager.unlink_agent_global("nonexistent.md")
    assert not success


def test_get_agent_link_status(temp_dirs):
    """Test checking link status."""
    agent_file, claude_dir = temp_dirs
    manager = SymlinkManager(claude_dir=claude_dir)

    # Before linking
    status = manager.get_agent_link_status(agent_file)
    assert not status["global_linked"]

    # After linking
    manager.link_agent_global(agent_file)
    status = manager.get_agent_link_status(agent_file)
    assert status["global_linked"]
