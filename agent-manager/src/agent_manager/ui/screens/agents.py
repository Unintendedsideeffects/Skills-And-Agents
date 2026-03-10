"""Agents screen for listing and managing agents."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, ListView, Button, Static
from textual.containers import Horizontal, Vertical
from textual.message import Message

from agent_manager.models import Agent
from agent_manager.ui.widgets.item_list import AgentListItem
from agent_manager.ui.widgets.preview_pane import PreviewPane


class AgentsScreen(Screen):
    """List and manage agents."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down"),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("g", "link_global", "Link Global"),
        Binding("u", "unlink", "Unlink"),
        Binding("slash", "focus_search", "Search"),
    ]

    class AgentSelected(Message):
        """Message sent when an agent is selected."""

        def __init__(self, agent: Agent) -> None:
            super().__init__()
            self.agent = agent

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._filter_text = ""
        self._selected_agent: Agent | None = None

    def compose(self) -> ComposeResult:
        """Compose the agents screen."""
        yield Header()
        yield Input(placeholder="Search agents... (press /)", id="search-input")

        with Horizontal(id="main-content"):
            with Vertical(id="list-container"):
                yield ListView(id="agent-list")
                with Horizontal(classes="pane-actions pane-actions-left"):
                    yield Button("Install All On Claude Code", id="bulk-install-claude-agent-btn")

            with Vertical(id="preview-column"):
                yield PreviewPane(id="preview-pane")
                with Horizontal(classes="pane-actions pane-actions-right"):
                    yield Static("", classes="action-spacer")
                    yield Button("Install On Claude Code", id="install-claude-agent-btn")
                    yield Button("Remove", id="remove-agent-btn", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.app.sub_title = "Agents"
        self._rebuild_list()
        # Focus the list for immediate keyboard navigation
        self.query_one("#agent-list", ListView).focus()

    def _rebuild_list(self) -> None:
        """Rebuild the agent list with current filter."""
        list_view = self.query_one("#agent-list", ListView)
        list_view.clear()

        agents = self.app.agents
        if self._filter_text:
            filter_lower = self._filter_text.lower()
            agents = [
                a for a in agents
                if filter_lower in a.metadata.name.lower()
                or filter_lower in a.metadata.description.lower()
            ]

        if not agents:
            # Show empty state
            preview = self.query_one("#preview-pane", PreviewPane)
            if self._filter_text:
                preview.show_message("No agents match your search")
            elif not self.app.config.scan_paths:
                preview.show_message("No scan paths configured\n\nPress [,] to add paths in Settings")
            else:
                preview.show_message("No agents found\n\nAdd .claude/agents/ folders to your scan paths")
            return

        for agent in agents:
            list_view.append(AgentListItem(agent))

        # Update preview if we have agents
        if agents and list_view.index is not None:
            self._update_preview_for_index(list_view.index)

    def _update_preview_for_index(self, index: int) -> None:
        """Update preview pane for the given list index."""
        list_view = self.query_one("#agent-list", ListView)
        if 0 <= index < len(list_view.children):
            item = list_view.children[index]
            if isinstance(item, AgentListItem):
                self._selected_agent = item.agent
                preview = self.query_one("#preview-pane", PreviewPane)
                preview.show_agent(item.agent)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        if isinstance(event.item, AgentListItem):
            self._selected_agent = event.item.agent
            preview = self.query_one("#preview-pane", PreviewPane)
            preview.show_agent(event.item.agent)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle list item highlight (cursor movement)."""
        if isinstance(event.item, AgentListItem):
            self._selected_agent = event.item.agent
            preview = self.query_one("#preview-pane", PreviewPane)
            preview.show_agent(event.item.agent)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self._filter_text = event.value
            self._rebuild_list()

    def action_cursor_down(self) -> None:
        """Move cursor down in the list."""
        list_view = self.query_one("#agent-list", ListView)
        list_view.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the list."""
        list_view = self.query_one("#agent-list", ListView)
        list_view.action_cursor_up()

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search = self.query_one("#search-input", Input)
        search.focus()

    def on_key(self, event) -> None:
        """Handle key events for search clearing."""
        # Clear search on escape when search is focused
        search = self.query_one("#search-input", Input)
        if event.key == "escape" and search.has_focus and self._filter_text:
            search.value = ""
            self._filter_text = ""
            self._rebuild_list()
            list_view = self.query_one("#agent-list", ListView)
            list_view.focus()
            event.stop()

    def action_link_global(self) -> None:
        """Install the selected agent to Claude Code."""
        self._install_selected_agent("claude")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle install/remove buttons."""
        button_id = event.button.id
        if button_id == "bulk-install-claude-agent-btn":
            self._install_all_agents("claude")
        elif button_id == "install-claude-agent-btn":
            self._install_selected_agent("claude")
        elif button_id == "remove-agent-btn":
            self.action_unlink()

    def _install_selected_agent(self, target: str) -> None:
        """Install the selected agent to one or more targets."""
        if not self._selected_agent:
            self.notify("No agent selected", severity="warning")
            return

        targets = ["claude", "codex"] if target == "all" else [target]
        outcomes: list[str] = []

        for current_target in targets:
            if current_target == "claude":
                result = self.app.symlink_manager.link_agent_global(
                    self._selected_agent.source_path
                )
                if result.value in {"success", "already_exists"}:
                    self._selected_agent.global_link = (
                        self.app.symlink_manager.global_agents_dir
                        / self._selected_agent.source_path.name
                    )
            else:
                result = self.app.symlink_manager.link_agent_codex(
                    self._selected_agent.source_path
                )
                if result.value in {"success", "already_exists"}:
                    self._selected_agent.codex_link = (
                        self.app.symlink_manager.codex_agents_dir
                        / self._selected_agent.source_path.name
                    )
            outcomes.append(f"{current_target}:{result.value}")

        self._refresh_selected_agent_view()
        self.notify(f"{self._selected_agent.metadata.name}: {', '.join(outcomes)}")

    def _install_all_agents(self, target: str) -> None:
        """Install all discovered agents to one or more targets."""
        agents = self.app.agents
        if not agents:
            self.notify("No agents available", severity="warning")
            return

        targets = ["claude", "codex"] if target == "all" else [target]
        successes = 0
        conflicts = 0

        for agent in agents:
            for current_target in targets:
                if current_target == "claude":
                    result = self.app.symlink_manager.link_agent_global(agent.source_path)
                    if result.value in {"success", "already_exists"}:
                        agent.global_link = (
                            self.app.symlink_manager.global_agents_dir / agent.source_path.name
                        )
                        successes += 1
                    elif result.value == "conflict":
                        conflicts += 1
                else:
                    result = self.app.symlink_manager.link_agent_codex(agent.source_path)
                    if result.value in {"success", "already_exists"}:
                        agent.codex_link = (
                            self.app.symlink_manager.codex_agents_dir / agent.source_path.name
                        )
                        successes += 1
                    elif result.value == "conflict":
                        conflicts += 1

        self._refresh_selected_agent_view()
        summary = f"Installed {len(agents)} agent(s)"
        if len(targets) > 1:
            summary += " on Claude Code and Codex"
        else:
            summary += f" on {targets[0]}"
        summary += f" ({successes} link operations"
        if conflicts:
            summary += f", {conflicts} conflicts"
        summary += ")"
        self.notify(summary)

    def action_unlink(self) -> None:
        """Remove the selected agent from Claude Code and Codex."""
        if not self._selected_agent:
            self.notify("No agent selected", severity="warning")
            return

        removed_claude = self.app.symlink_manager.unlink_agent_global(
            self._selected_agent.source_path.name
        )
        removed_codex = self.app.symlink_manager.unlink_agent_codex(
            self._selected_agent.source_path.name
        )

        if removed_claude or removed_codex:
            self._selected_agent.global_link = None
            self._selected_agent.codex_link = None
            self._refresh_selected_agent_view()
            self.notify(f"Removed {self._selected_agent.metadata.name}")
        else:
            self.notify("Agent is not installed", severity="information")

    def _refresh_selected_agent_view(self) -> None:
        """Refresh list and preview after agent changes."""
        self._rebuild_list()
        if self._selected_agent:
            preview = self.query_one("#preview-pane", PreviewPane)
            preview.show_agent(self._selected_agent)
