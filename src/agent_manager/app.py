"""Main Textual application for Agent Manager."""

from textual.app import ComposeResult, App
from textual.binding import Binding
from textual.widgets import Header, Footer

from agent_manager.core import ConfigManager, AgentSkillScanner, SymlinkManager, MCPManager, SessionManager
from agent_manager.models import Agent, Skill, AppConfig, MCPServer
from agent_manager.ui.screens import (
    DashboardScreen,
    AgentsScreen,
    SkillsScreen,
    SettingsScreen,
    MCPScreen,
    SessionsScreen,
)


class AgentManagerApp(App):
    """Main TUI application for managing agents and skills."""

    TITLE = "Agent Manager"
    SUB_TITLE = "Manage Claude Code Agents and Skills"

    CSS_PATH = "ui/styles/theme.tcss"

    BINDINGS = [
        Binding("d", "goto('dashboard')", "Dashboard", show=True),
        Binding("a", "goto('agents')", "Agents", show=True),
        Binding("s", "goto('skills')", "Skills", show=True),
        Binding("m", "goto('mcp')", "MCP", show=True),
        Binding("p", "goto('sessions')", "Sessions", show=True),
        Binding("comma", "goto('settings')", "Settings", show=True),
        Binding("escape", "go_back", "Back", show=True, priority=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    SCREENS = {
        "dashboard": DashboardScreen,
        "agents": AgentsScreen,
        "skills": SkillsScreen,
        "mcp": MCPScreen,
        "sessions": SessionsScreen,
        "settings": SettingsScreen,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self.scanner = AgentSkillScanner()
        self.symlink_manager = SymlinkManager(
            claude_dir=self.config.claude_dir,
        )
        self.mcp_manager = MCPManager()
        self.session_manager = SessionManager()
        self.agents: list[Agent] = []
        self.skills: list[Skill] = []

    def compose(self) -> ComposeResult:
        """Compose the app."""
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        """Called when app starts."""
        await self.push_screen("dashboard")
        # Start initial scan in the background
        self.run_worker(self.scan_all(), exclusive=True)

    async def scan_all(self) -> None:
        """Scan all configured paths for agents and skills."""
        if not self.config.scan_paths:
            self.notify(
                "No scan paths configured. Go to Settings (,) to add paths.",
                severity="warning",
            )
            return

        # Get enabled paths
        enabled_paths = [
            sp.path for sp in self.config.scan_paths if sp.enabled
        ]

        if not enabled_paths:
            self.notify("No enabled scan paths.", severity="warning")
            return

        try:
            # Run async scan
            result = await self.scanner.scan_all(enabled_paths)

            self.agents = result.agents
            self.skills = result.skills

            # Update symlink status for each agent and skill
            for agent in self.agents:
                status = self.symlink_manager.get_agent_link_status(agent.source_path)
                agent.global_link = status.get("global_target")

            for skill in self.skills:
                status = self.symlink_manager.get_skill_link_status(skill.source_dir)
                skill.global_link = status.get("global_target")

            # Update scan path stats
            for scan_path in self.config.scan_paths:
                scan_path.agent_count = sum(
                    1 for a in self.agents
                    if str(a.source_repo).startswith(str(scan_path.path))
                )
                scan_path.skill_count = sum(
                    1 for s in self.skills
                    if str(s.source_repo).startswith(str(scan_path.path))
                )

            # Save updated config
            self.config_manager.save(self.config)

            # Notify current screen of update
            screen = self.screen
            if hasattr(screen, "update_stats"):
                screen.update_stats()
            elif hasattr(screen, "_rebuild_list"):
                screen._rebuild_list()

            # Report any errors
            if result.errors:
                error_count = len(result.errors)
                self.notify(
                    f"Scan complete with {error_count} error(s)",
                    severity="warning",
                )
            else:
                agent_count = len(self.agents)
                skill_count = len(self.skills)
                self.notify(
                    f"Found {agent_count} agent(s) and {skill_count} skill(s)"
                )

        except Exception as e:
            self.notify(f"Scan failed: {e}", severity="error")

    def action_goto(self, screen_name: str) -> None:
        """Navigate to a named screen using switch (not push)."""
        try:
            self.switch_screen(screen_name)
        except ValueError:
            self.notify(f"Unknown screen: {screen_name}", severity="error")

    def action_go_back(self) -> None:
        """Go back to the previous screen, or to dashboard."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
        else:
            # If on the only screen, go to dashboard
            if self.screen.name != "dashboard":
                self.switch_screen("dashboard")

    def action_refresh(self) -> None:
        """Trigger a refresh scan."""
        self.run_worker(self.scan_all(), exclusive=True)


def main():
    """Run the application."""
    app = AgentManagerApp()
    app.run()


if __name__ == "__main__":
    main()
