"""Skills screen for listing and managing skills."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, ListView, Button
from textual.containers import Horizontal, Vertical

from agent_manager.models import Skill
from agent_manager.ui.widgets.item_list import SkillListItem
from agent_manager.ui.widgets.preview_pane import PreviewPane


class SkillsScreen(Screen):
    """List and manage skills."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down"),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("g", "link_global", "Link Global"),
        Binding("u", "unlink", "Unlink"),
        Binding("slash", "focus_search", "Search"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._filter_text = ""
        self._selected_skill: Skill | None = None

    def compose(self) -> ComposeResult:
        """Compose the skills screen."""
        yield Header()
        yield Input(placeholder="Search skills... (press /)", id="search-input")

        with Horizontal(id="main-content"):
            with Vertical(id="list-container"):
                yield ListView(id="skill-list")
                with Horizontal(classes="pane-actions pane-actions-left"):
                    yield Button("Install All On Both", id="bulk-install-all-skill-btn")
                    yield Button("Install All On Codex", id="bulk-install-codex-skill-btn")
                    yield Button("Install All On Claude Code", id="bulk-install-claude-skill-btn")

            with Vertical(id="preview-column"):
                yield PreviewPane(id="preview-pane")
                with Horizontal(classes="pane-actions pane-actions-right"):
                    yield Static("", classes="action-spacer")
                    yield Button("Install On Both", id="install-all-skill-btn")
                    yield Button("Install On Codex", id="install-codex-skill-btn")
                    yield Button("Install On Claude Code", id="install-claude-skill-btn")
                    yield Button("Remove", id="remove-skill-btn", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.app.sub_title = "Skills"
        self._rebuild_list()
        # Focus the list for immediate keyboard navigation
        self.query_one("#skill-list", ListView).focus()

    def _rebuild_list(self) -> None:
        """Rebuild the skill list with current filter."""
        list_view = self.query_one("#skill-list", ListView)
        list_view.clear()

        skills = self.app.skills
        if self._filter_text:
            filter_lower = self._filter_text.lower()
            skills = [
                s for s in skills
                if filter_lower in s.metadata.name.lower()
                or filter_lower in s.metadata.description.lower()
            ]

        if not skills:
            # Show empty state
            preview = self.query_one("#preview-pane", PreviewPane)
            if self._filter_text:
                preview.show_message("No skills match your search")
            elif not self.app.config.scan_paths:
                preview.show_message("No scan paths configured\n\nPress [,] to add paths in Settings")
            else:
                preview.show_message("No skills found\n\nAdd .claude/skills/ folders to your scan paths")
            return

        for skill in skills:
            list_view.append(SkillListItem(skill))

        # Update preview if we have skills
        if skills and list_view.index is not None:
            self._update_preview_for_index(list_view.index)

    def _update_preview_for_index(self, index: int) -> None:
        """Update preview pane for the given list index."""
        list_view = self.query_one("#skill-list", ListView)
        if 0 <= index < len(list_view.children):
            item = list_view.children[index]
            if isinstance(item, SkillListItem):
                self._selected_skill = item.skill
                preview = self.query_one("#preview-pane", PreviewPane)
                preview.show_skill(item.skill)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        if isinstance(event.item, SkillListItem):
            self._selected_skill = event.item.skill
            preview = self.query_one("#preview-pane", PreviewPane)
            preview.show_skill(event.item.skill)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle list item highlight (cursor movement)."""
        if isinstance(event.item, SkillListItem):
            self._selected_skill = event.item.skill
            preview = self.query_one("#preview-pane", PreviewPane)
            preview.show_skill(event.item.skill)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self._filter_text = event.value
            self._rebuild_list()

    def action_cursor_down(self) -> None:
        """Move cursor down in the list."""
        list_view = self.query_one("#skill-list", ListView)
        list_view.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the list."""
        list_view = self.query_one("#skill-list", ListView)
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
            list_view = self.query_one("#skill-list", ListView)
            list_view.focus()
            event.stop()

    def action_link_global(self) -> None:
        """Install the selected skill to Claude Code."""
        self._install_selected_skill("claude")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle install/remove buttons."""
        button_id = event.button.id
        if button_id == "bulk-install-all-skill-btn":
            self._install_all_skills("all")
        elif button_id == "bulk-install-codex-skill-btn":
            self._install_all_skills("codex")
        elif button_id == "bulk-install-claude-skill-btn":
            self._install_all_skills("claude")
        elif button_id == "install-all-skill-btn":
            self._install_selected_skill("all")
        elif button_id == "install-codex-skill-btn":
            self._install_selected_skill("codex")
        elif button_id == "install-claude-skill-btn":
            self._install_selected_skill("claude")
        elif button_id == "remove-skill-btn":
            self.action_unlink()

    def _install_selected_skill(self, target: str) -> None:
        """Install the selected skill to one or more targets."""
        if not self._selected_skill:
            self.notify("No skill selected", severity="warning")
            return

        targets = ["claude", "codex"] if target == "all" else [target]
        outcomes: list[str] = []

        for current_target in targets:
            if current_target == "claude":
                result = self.app.symlink_manager.link_skill_global(
                    self._selected_skill.source_dir
                )
                if result.value in {"success", "already_exists"}:
                    self._selected_skill.global_link = (
                        self.app.symlink_manager.global_skills_dir
                        / self._selected_skill.source_dir.name
                    )
            else:
                result = self.app.symlink_manager.link_skill_codex(
                    self._selected_skill.source_dir
                )
                if result.value in {"success", "already_exists"}:
                    self._selected_skill.codex_link = (
                        self.app.symlink_manager.codex_skills_dir
                        / self._selected_skill.source_dir.name
                    )
            outcomes.append(f"{current_target}:{result.value}")

        self._refresh_selected_skill_view()
        self.notify(f"{self._selected_skill.metadata.name}: {', '.join(outcomes)}")

    def _install_all_skills(self, target: str) -> None:
        """Install all discovered skills to one or more targets."""
        skills = self.app.skills
        if not skills:
            self.notify("No skills available", severity="warning")
            return

        targets = ["claude", "codex"] if target == "all" else [target]
        successes = 0
        conflicts = 0

        for skill in skills:
            for current_target in targets:
                if current_target == "claude":
                    result = self.app.symlink_manager.link_skill_global(skill.source_dir)
                    if result.value in {"success", "already_exists"}:
                        skill.global_link = (
                            self.app.symlink_manager.global_skills_dir / skill.source_dir.name
                        )
                        successes += 1
                    elif result.value == "conflict":
                        conflicts += 1
                else:
                    result = self.app.symlink_manager.link_skill_codex(skill.source_dir)
                    if result.value in {"success", "already_exists"}:
                        skill.codex_link = (
                            self.app.symlink_manager.codex_skills_dir / skill.source_dir.name
                        )
                        successes += 1
                    elif result.value == "conflict":
                        conflicts += 1

        self._refresh_selected_skill_view()
        summary = f"Installed {len(skills)} skill(s)"
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
        """Remove the selected skill from Claude Code and Codex."""
        if not self._selected_skill:
            self.notify("No skill selected", severity="warning")
            return

        removed_claude = self.app.symlink_manager.unlink_skill_global(
            self._selected_skill.source_dir.name
        )
        removed_codex = self.app.symlink_manager.unlink_skill_codex(
            self._selected_skill.source_dir.name
        )

        if removed_claude or removed_codex:
            self._selected_skill.global_link = None
            self._selected_skill.codex_link = None
            self._refresh_selected_skill_view()
            self.notify(f"Removed {self._selected_skill.metadata.name}")
        else:
            self.notify("Skill is not installed", severity="information")

    def _refresh_selected_skill_view(self) -> None:
        """Refresh list and preview after skill changes."""
        self._rebuild_list()
        if self._selected_skill:
            preview = self.query_one("#preview-pane", PreviewPane)
            preview.show_skill(self._selected_skill)
