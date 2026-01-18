"""Skills screen for listing and managing skills."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, ListView
from textual.containers import Horizontal, Vertical

from agent_manager.models import Skill
from agent_manager.ui.widgets.item_list import SkillListItem
from agent_manager.ui.widgets.preview_pane import PreviewPane


class SkillsScreen(Screen):
    """List and manage skills."""

    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("g", "link_global", "Link Global"),
        ("u", "unlink", "Unlink"),
        ("slash", "focus_search", "Search"),
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

            yield PreviewPane(id="preview-pane")

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
        """Link the selected skill globally."""
        if not self._selected_skill:
            self.notify("No skill selected", severity="warning")
            return

        result = self.app.symlink_manager.link_skill_global(
            self._selected_skill.source_dir
        )

        if result.value == "success":
            self._selected_skill.global_link = (
                self.app.symlink_manager.global_skills_dir
                / self._selected_skill.source_dir.name
            )
            self.notify(f"Linked {self._selected_skill.metadata.name} globally")
            self._rebuild_list()
        elif result.value == "already_exists":
            self.notify("Already linked globally", severity="information")
        elif result.value == "conflict":
            self.notify("Conflict: different skill exists at target", severity="error")
        else:
            self.notify(f"Failed to link: {result.value}", severity="error")

    def action_unlink(self) -> None:
        """Unlink the selected skill."""
        if not self._selected_skill:
            self.notify("No skill selected", severity="warning")
            return

        if self._selected_skill.global_link:
            success = self.app.symlink_manager.unlink_skill_global(
                self._selected_skill.source_dir.name
            )
            if success:
                self._selected_skill.global_link = None
                self.notify(f"Unlinked {self._selected_skill.metadata.name}")
                self._rebuild_list()
            else:
                self.notify("Failed to unlink", severity="error")
        else:
            self.notify("Skill is not linked", severity="information")
