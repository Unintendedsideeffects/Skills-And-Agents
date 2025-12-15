"""List item widgets for agents, skills, and MCP servers."""

from textual.app import ComposeResult
from textual.widgets import ListItem, Static
from textual.containers import Horizontal

from agent_manager.models import Agent, Skill, LinkScope
from agent_manager.models.mcp_server import MCPServer, SyncStatus


class AgentListItem(ListItem):
    """A single agent entry in the list."""

    def __init__(self, agent: Agent, **kwargs) -> None:
        super().__init__(**kwargs)
        self.agent = agent

    def compose(self) -> ComposeResult:
        """Compose the agent list item."""
        color_class = f"color-{self.agent.metadata.color}"
        badge_class = f"badge-{self.agent.link_status.value}"
        badge_text = self._get_badge_text()

        with Horizontal(classes="item-row"):
            yield Static(f"●", classes=f"item-color-dot {color_class}")
            yield Static(self.agent.metadata.name, classes="item-name")
            yield Static(self.agent.metadata.model, classes="item-model")
            if badge_text:
                yield Static(badge_text, classes=f"badge {badge_class}")

    def _get_badge_text(self) -> str:
        """Get badge text based on link status."""
        status = self.agent.link_status
        if status == LinkScope.GLOBAL:
            return "GLOBAL"
        elif status == LinkScope.PROJECT:
            return "PROJECT"
        return ""


class SkillListItem(ListItem):
    """A single skill entry in the list."""

    def __init__(self, skill: Skill, **kwargs) -> None:
        super().__init__(**kwargs)
        self.skill = skill

    def compose(self) -> ComposeResult:
        """Compose the skill list item."""
        badge_class = f"badge-{self.skill.link_status.value}"
        badge_text = self._get_badge_text()

        with Horizontal(classes="item-row"):
            yield Static("◆", classes="item-color-dot color-purple")
            yield Static(self.skill.metadata.name, classes="item-name")
            yield Static(f"{len(self.skill.scripts)} scripts", classes="item-model")
            if badge_text:
                yield Static(badge_text, classes=f"badge {badge_class}")

    def _get_badge_text(self) -> str:
        """Get badge text based on link status."""
        status = self.skill.link_status
        if status == LinkScope.GLOBAL:
            return "GLOBAL"
        elif status == LinkScope.PROJECT:
            return "PROJECT"
        return ""


class MCPServerListItem(ListItem):
    """A single MCP server entry in the list."""

    def __init__(self, server: MCPServer, **kwargs) -> None:
        super().__init__(**kwargs)
        self.server = server

    def compose(self) -> ComposeResult:
        """Compose the MCP server list item."""
        # Status dot: ● enabled, ○ disabled
        dot = "●" if self.server.enabled else "○"
        dot_class = "color-green" if self.server.enabled else "color-gray"

        # Sync badge
        badge_text, badge_class = self._get_badge_info()

        with Horizontal(classes="item-row"):
            yield Static(dot, classes=f"item-color-dot {dot_class}")
            yield Static(self.server.id, classes="item-name")
            yield Static(self.server.transport, classes="item-model")
            if badge_text:
                yield Static(badge_text, classes=f"badge {badge_class}")

    def _get_badge_info(self) -> tuple[str, str]:
        """Get badge text and class based on sync status."""
        status = self.server.sync_status

        if status == SyncStatus.SYNCED:
            return "SYNCED", "badge-synced"
        elif status == SyncStatus.PARTIAL:
            return "PARTIAL", "badge-partial"
        elif status == SyncStatus.DISABLED:
            return "DISABLED", "badge-disabled"
        else:
            return "", ""
