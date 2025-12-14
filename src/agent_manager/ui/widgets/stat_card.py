"""Stat card widget for dashboard."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static


class StatCard(Vertical):
    """A statistics card showing a value and label."""

    DEFAULT_CSS = """
    StatCard {
        background: $surface;
        border: solid $border;
        margin: 0 1 1 0;
        padding: 1 2;
        height: 7;
        width: 1fr;
    }
    """

    def __init__(
        self,
        label: str,
        value: str | int = "0",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._label = label
        self._value = str(value)

    def compose(self) -> ComposeResult:
        """Compose the stat card."""
        yield Static(self._value, id="stat-value", classes="stat-value")
        yield Static(self._label, id="stat-label", classes="stat-label")

    def update_value(self, value: str | int) -> None:
        """Update the displayed value."""
        self._value = str(value)
        value_widget = self.query_one("#stat-value", Static)
        value_widget.update(self._value)
