"""Tests for YAML frontmatter parser."""

import pytest
from pathlib import Path
from agent_manager.core.parser import FrontmatterParser


@pytest.fixture
def parser():
    """Create a parser instance."""
    return FrontmatterParser()


def test_parse_valid_frontmatter(parser):
    """Test parsing valid frontmatter."""
    content = """---
name: test-agent
description: A test agent
model: sonnet
color: blue
---

This is the body content."""

    fm, body = parser.parse_string(content)
    assert fm["name"] == "test-agent"
    assert fm["description"] == "A test agent"
    assert fm["model"] == "sonnet"
    assert fm["color"] == "blue"
    assert "This is the body content." in body


def test_parse_missing_frontmatter(parser):
    """Test error on missing frontmatter."""
    content = "Just body content without frontmatter"
    with pytest.raises(ValueError, match="No frontmatter found"):
        parser.parse_string(content)


def test_parse_empty_frontmatter(parser):
    """Test error on empty frontmatter."""
    content = """---
---

Body content"""
    with pytest.raises(ValueError, match="Empty frontmatter"):
        parser.parse_string(content)


def test_parse_invalid_yaml(parser):
    """Test error on invalid YAML."""
    content = """---
name: test
invalid: [unclosed array
---

Body"""
    with pytest.raises(ValueError, match="Invalid YAML"):
        parser.parse_string(content)


def test_serialize_roundtrip(parser):
    """Test serialize and parse roundtrip."""
    original = {
        "name": "test-agent",
        "description": "Test description",
        "model": "sonnet",
        "color": "blue",
    }
    body = "This is the system prompt"

    serialized = parser.serialize(original, body)
    fm, body_out = parser.parse_string(serialized)

    assert fm["name"] == original["name"]
    assert fm["description"] == original["description"]
    assert body_out.strip() == body
