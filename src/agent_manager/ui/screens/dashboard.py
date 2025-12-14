"""Dashboard screen showing overview statistics."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import Horizontal, Vertical, Container

from agent_manager.ui.widgets.stat_card import StatCard


class DashboardScreen(Screen):
    """Main dashboard showing overview statistics."""

    BINDINGS = [
        ("a", "app.push_screen('agents')", "Agents"),
        ("s", "app.push_screen('skills')", "Skills"),
        ("comma", "app.push_screen('settings')", "Settings"),
        ("r", "refresh", "Refresh"),
        ("q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the dashboard screen."""
        yield Header()

        with Container(id="dashboard-content"):
            # Stats row
            with Horizontal(id="stats-row"):
                yield StatCard("Agents", "0", id="agents-count")
                yield StatCard("Skills", "0", id="skills-count")
                yield StatCard("Global", "0", id="global-count")
                yield StatCard("Scan Paths", "0", id="paths-count")

            # Quick info section
            with Vertical(classes="content-panel"):
                yield Static("Agent Manager", classes="preview-title")
                yield Static(
                    "Press [bold]a[/] for Agents, [bold]s[/] for Skills, "
                    "[bold],[/] for Settings, [bold]r[/] to Refresh",
                    classes="preview-meta",
                )

            # Recent activity / scan paths section
            with Vertical(classes="content-panel"):
                yield Static("Scan Paths", classes="preview-title")
                yield Static("No scan paths configured", id="paths-list")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.update_stats()

    def update_stats(self) -> None:
        """Update statistics from app state."""
        app = self.app

        # Update agent count
        agents_card = self.query_one("#agents-count", StatCard)
        agents_card.update_value(len(app.agents))

        # Update skill count
        skills_card = self.query_one("#skills-count", StatCard)
        skills_card.update_value(len(app.skills))

        # Update global count
        global_count = sum(1 for a in app.agents if a.global_link)
        global_count += sum(1 for s in app.skills if s.global_link)
        global_card = self.query_one("#global-count", StatCard)
        global_card.update_value(global_count)

        # Update paths count
        paths_card = self.query_one("#paths-count", StatCard)
        paths_card.update_value(len(app.config.scan_paths))

        # Update paths list
        paths_list = self.query_one("#paths-list", Static)
        if app.config.scan_paths:
            paths_text = "\n".join(
                f"  {'✓' if sp.enabled else '✗'} {sp.path}"
                for sp in app.config.scan_paths
            )
            paths_list.update(paths_text)
        else:
            paths_list.update("No scan paths configured. Press [bold],[/] to add paths.")

    def action_refresh(self) -> None:
        """Refresh the dashboard."""
        self.app.run_worker(self.app.scan_all())
        self.notify("Refreshing...")
