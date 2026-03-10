"""Startup loading screen."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, LoadingIndicator, Static


class LoadingScreen(Screen):
    """Shown while the initial scan is running."""

    def compose(self) -> ComposeResult:
        """Compose the loading screen."""
        yield Header()
        with Vertical(id="loading-screen"):
            yield Static("Agent Manager", classes="loading-title")
            yield Static(
                "Scanning configured paths for agents and skills...",
                classes="loading-subtitle",
            )
            yield LoadingIndicator(id="loading-indicator")
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.app.sub_title = "Loading"
