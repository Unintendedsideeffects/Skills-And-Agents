"""Preview pane widget for viewing agent/skill content."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, Markdown

from agent_manager.models import Agent, Skill


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

        md = f"""# {agent.metadata.name}

**Model:** `{agent.metadata.model}`
**Color:** {agent.metadata.color}
**Source:** `{agent.source_path}`

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

        md = f"""# {skill.metadata.name}

**Source:** `{skill.source_dir}`

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
