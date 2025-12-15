"""Preview pane widget for viewing agent/skill content."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, Markdown

from agent_manager.models import Agent, Skill
from agent_manager.models.mcp_server import MCPServer, SyncStatus, TARGETS


def _shorten_path(path: Path) -> str:
    """Shorten path for display, using ~ for home directory."""
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


class PreviewPane(VerticalScroll):
    """Preview agent/skill content with markdown rendering."""

    def compose(self) -> ComposeResult:
        """Compose the preview pane."""
        yield Static(
            "Select an item to preview",
            id="preview-placeholder",
            classes="preview-title",
        )
        yield Markdown("", id="preview-content")

    def show_agent(self, agent: Agent) -> None:
        """Update preview with agent details."""
        placeholder = self.query_one("#preview-placeholder", Static)
        content = self.query_one("#preview-content", Markdown)

        placeholder.display = False
        content.display = True

        # Build markdown preview
        link_info = self._format_link_status(agent)
        prompt_preview = agent.prompt[:800] + "..." if len(agent.prompt) > 800 else agent.prompt
        source_display = _shorten_path(agent.source_path)

        md = f"""# {agent.metadata.name}

**Model:** `{agent.metadata.model}`
**Color:** {agent.metadata.color}
**Source:** `{source_display}`

{link_info}

## Description

{agent.metadata.description[:300]}{"..." if len(agent.metadata.description) > 300 else ""}

## System Prompt

```
{prompt_preview}
```
"""
        content.update(md)

    def show_skill(self, skill: Skill) -> None:
        """Update preview with skill details."""
        placeholder = self.query_one("#preview-placeholder", Static)
        content = self.query_one("#preview-content", Markdown)

        placeholder.display = False
        content.display = True

        # Build markdown preview
        link_info = self._format_skill_link_status(skill)
        scripts_list = "\n".join(f"- `{s.name}`" for s in skill.scripts) or "None"
        source_display = _shorten_path(skill.source_dir)

        md = f"""# {skill.metadata.name}

**Source:** `{source_display}`

{link_info}

## Description

{skill.metadata.description}

## Scripts

{scripts_list}

## Content

{skill.content[:500]}{"..." if len(skill.content) > 500 else ""}
"""
        content.update(md)

    def clear(self) -> None:
        """Clear the preview pane."""
        placeholder = self.query_one("#preview-placeholder", Static)
        content = self.query_one("#preview-content", Markdown)

        placeholder.display = True
        content.display = False
        content.update("")

    def show_message(self, message: str) -> None:
        """Show a simple message in the preview pane."""
        placeholder = self.query_one("#preview-placeholder", Static)
        content = self.query_one("#preview-content", Markdown)

        placeholder.display = False
        content.display = True
        content.update(message)

    def _format_link_status(self, agent: Agent) -> str:
        """Format link status for display."""
        status = agent.link_status.value.upper()
        if agent.global_link:
            return f"**Status:** 🟢 {status} (`~/.claude/agents/`)"
        elif agent.project_links:
            projects = len(agent.project_links)
            return f"**Status:** 🟡 {status} ({projects} project{'s' if projects > 1 else ''})"
        return "**Status:** ⚪ UNLINKED"

    def _format_skill_link_status(self, skill: Skill) -> str:
        """Format link status for display."""
        status = skill.link_status.value.upper()
        if skill.global_link:
            return f"**Status:** 🟢 {status} (`~/.claude/skills/`)"
        elif skill.project_links:
            projects = len(skill.project_links)
            return f"**Status:** 🟡 {status} ({projects} project{'s' if projects > 1 else ''})"
        return "**Status:** ⚪ UNLINKED"

    def show_mcp_server(self, server: MCPServer) -> None:
        """Update preview with MCP server details."""
        placeholder = self.query_one("#preview-placeholder", Static)
        content = self.query_one("#preview-content", Markdown)

        placeholder.display = False
        content.display = True

        # Build sync status display
        sync_status = self._format_mcp_sync_status(server)

        # Build environment display
        env_display = ""
        if server.env:
            env_lines = [f"  {k}={v}" for k, v in server.env.items()]
            env_display = "\n".join(env_lines)
        else:
            env_display = "  (none)"

        # Build tags display
        tags_display = ", ".join(server.tags) if server.tags else "(none)"

        # Build args display
        args_display = " ".join(server.args) if server.args else "(none)"

        md = f"""# {server.display_name}

**ID:** `{server.id}`
**Command:** `{server.command}`
**Transport:** {server.transport}
**Type:** {server.type}
**Enabled:** {"Yes" if server.enabled else "No"}

## Sync Status

{sync_status}

## Arguments

```
{args_display}
```

## Environment

```
{env_display}
```

## Tags

{tags_display}
"""
        content.update(md)

    def _format_mcp_sync_status(self, server: MCPServer) -> str:
        """Format MCP sync status as a grid."""
        if not server.synced_to:
            return "Not synced to any targets"

        lines = []
        for target, display_name in TARGETS.items():
            synced = server.synced_to.get(target, False)
            icon = "✓" if synced else "✗"
            lines.append(f"  {icon} {display_name}")

        return "\n".join(lines)
