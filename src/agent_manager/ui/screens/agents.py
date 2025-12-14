"""Agents screen for listing and managing agents."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, ListView, Static
from textual.containers import Horizontal, Vertical
from textual.message import Message

from agent_manager.models import Agent
from agent_manager.ui.widgets.item_list import AgentListItem
from agent_manager.ui.widgets.preview_pane import PreviewPane


class AgentsScreen(Screen):
    """List and manage agents."""

    BINDINGS = [
        ("d", "app.push_screen('dashboard')", "Dashboard"),
        ("s", "app.push_screen('skills')", "Skills"),
        ("comma", "app.push_screen('settings')", "Settings"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("g", "link_global", "Link Global"),
        ("u", "unlink", "Unlink"),
        ("slash", "focus_search", "Search"),
        ("escape", "clear_search", "Clear"),
        ("r", "refresh", "Refresh"),
        ("q", "app.quit", "Quit"),
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

            yield PreviewPane(id="preview-pane")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self._rebuild_list()

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

    def action_clear_search(self) -> None:
        """Clear search and refocus list."""
        search = self.query_one("#search-input", Input)
        search.value = ""
        self._filter_text = ""
        self._rebuild_list()
        list_view = self.query_one("#agent-list", ListView)
        list_view.focus()

    def action_link_global(self) -> None:
        """Link the selected agent globally."""
        if not self._selected_agent:
            self.notify("No agent selected", severity="warning")
            return

        result = self.app.symlink_manager.link_agent_global(
            self._selected_agent.source_path
        )

        if result.value == "success":
            self._selected_agent.global_link = (
                self.app.symlink_manager.global_agents_dir
                / self._selected_agent.source_path.name
            )
            self.notify(f"Linked {self._selected_agent.metadata.name} globally")
            self._rebuild_list()
        elif result.value == "already_exists":
            self.notify("Already linked globally", severity="information")
        elif result.value == "conflict":
            self.notify("Conflict: different agent exists at target", severity="error")
        else:
            self.notify(f"Failed to link: {result.value}", severity="error")

    def action_unlink(self) -> None:
        """Unlink the selected agent."""
        if not self._selected_agent:
            self.notify("No agent selected", severity="warning")
            return

        if self._selected_agent.global_link:
            success = self.app.symlink_manager.unlink_agent_global(
                self._selected_agent.source_path.name
            )
            if success:
                self._selected_agent.global_link = None
                self.notify(f"Unlinked {self._selected_agent.metadata.name}")
                self._rebuild_list()
            else:
                self.notify("Failed to unlink", severity="error")
        else:
            self.notify("Agent is not linked", severity="information")

    def action_refresh(self) -> None:
        """Refresh the agent list."""
        self.app.run_worker(self.app.scan_all())
        self.notify("Refreshing...")
