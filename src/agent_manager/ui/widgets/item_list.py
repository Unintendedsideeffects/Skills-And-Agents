"""List item widgets for agents and skills."""

from textual.app import ComposeResult
from textual.widgets import ListItem, Static
from textual.containers import Horizontal

from agent_manager.models import Agent, Skill, LinkScope


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
