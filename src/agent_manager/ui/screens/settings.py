"""Settings screen for configuring the agent manager."""

from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, ListView, ListItem
from textual.containers import Horizontal, Vertical


class PathListItem(ListItem):
    """A scan path entry in the list."""

    def __init__(self, path: Path, enabled: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.path = path
        self.enabled = enabled

    def compose(self) -> ComposeResult:
        """Compose the path list item."""
        status = "✓" if self.enabled else "✗"
        status_class = "path-enabled" if self.enabled else "path-disabled"
        with Horizontal(classes="item-row"):
            yield Static(status, classes=f"item-color-dot {status_class}")
            yield Static(str(self.path), classes="item-name")


class SettingsScreen(Screen):
    """Settings and configuration screen."""

    BINDINGS = [
        ("d", "app.push_screen('dashboard')", "Dashboard"),
        ("a", "app.push_screen('agents')", "Agents"),
        ("s", "app.push_screen('skills')", "Skills"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("x", "remove_path", "Remove"),
        ("t", "toggle_path", "Toggle"),
        ("q", "app.quit", "Quit"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._selected_path: Path | None = None

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        yield Header()

        with Vertical(classes="settings-section"):
            yield Static("Scan Paths", classes="settings-title")
            yield Static(
                "These directories will be scanned for .claude/agents and .claude/skills",
                classes="preview-meta",
            )
            yield ListView(id="paths-list")

            with Horizontal():
                yield Input(
                    placeholder="Enter path to add (e.g., ~/Code)",
                    id="path-input",
                )
                yield Button("Add", id="add-path-btn", variant="primary")

        with Vertical(classes="settings-section"):
            yield Static("Preferences", classes="settings-title")
            yield Static(
                f"Config directory: {self.app.config.config_dir}",
                classes="preview-meta",
            )
            yield Static(
                f"Claude directory: {self.app.config.claude_dir}",
                classes="preview-meta",
            )

        with Vertical(classes="settings-section"):
            yield Static("Actions", classes="settings-title")
            with Horizontal():
                yield Button("Scan Now", id="scan-btn")
                yield Button("Save Config", id="save-btn")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self._rebuild_paths_list()

    def _rebuild_paths_list(self) -> None:
        """Rebuild the paths list from config."""
        list_view = self.query_one("#paths-list", ListView)
        list_view.clear()

        for scan_path in self.app.config.scan_paths:
            list_view.append(PathListItem(scan_path.path, scan_path.enabled))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle path selection."""
        if isinstance(event.item, PathListItem):
            self._selected_path = event.item.path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add-path-btn":
            self._add_path()
        elif event.button.id == "scan-btn":
            self._trigger_scan()
        elif event.button.id == "save-btn":
            self._save_config()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in path input."""
        if event.input.id == "path-input":
            self._add_path()

    def _add_path(self) -> None:
        """Add a new scan path."""
        path_input = self.query_one("#path-input", Input)
        path_str = path_input.value.strip()

        if not path_str:
            self.notify("Please enter a path", severity="warning")
            return

        path = Path(path_str).expanduser().resolve()

        if not path.exists():
            self.notify(f"Path does not exist: {path}", severity="error")
            return

        if not path.is_dir():
            self.notify(f"Path is not a directory: {path}", severity="error")
            return

        # Add to config
        added = self.app.config_manager.add_scan_path(self.app.config, path)
        if added:
            self._rebuild_paths_list()
            path_input.value = ""
            self.notify(f"Added: {path}")
        else:
            self.notify("Path already in list", severity="information")

    def action_remove_path(self) -> None:
        """Remove the selected scan path."""
        if not self._selected_path:
            self.notify("No path selected", severity="warning")
            return

        removed = self.app.config_manager.remove_scan_path(
            self.app.config, self._selected_path
        )
        if removed:
            self._rebuild_paths_list()
            self._selected_path = None
            self.notify("Path removed")
        else:
            self.notify("Failed to remove path", severity="error")

    def action_toggle_path(self) -> None:
        """Toggle the selected scan path enabled/disabled."""
        if not self._selected_path:
            self.notify("No path selected", severity="warning")
            return

        for sp in self.app.config.scan_paths:
            if sp.path.resolve() == self._selected_path.resolve():
                sp.enabled = not sp.enabled
                self._rebuild_paths_list()
                status = "enabled" if sp.enabled else "disabled"
                self.notify(f"Path {status}")
                return

    def action_cursor_down(self) -> None:
        """Move cursor down in the list."""
        list_view = self.query_one("#paths-list", ListView)
        list_view.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the list."""
        list_view = self.query_one("#paths-list", ListView)
        list_view.action_cursor_up()

    def _trigger_scan(self) -> None:
        """Trigger a full scan."""
        self.app.run_worker(self.app.scan_all())
        self.notify("Scanning...")

    def _save_config(self) -> None:
        """Save current configuration to disk."""
        self.app.config_manager.save(self.app.config)
        self.notify("Configuration saved")
