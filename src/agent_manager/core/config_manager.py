"""Configuration persistence for Agent Manager."""

import json
from pathlib import Path

from agent_manager.models import AppConfig, ScanPath


class ConfigManager:
    """
    Manages application configuration persistence.

    Config Location: ~/.config/agent-manager/
    Files:
    - config.json: Main configuration
    """

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize config manager.

        Args:
            config_dir: Override config directory (default: ~/.config/agent-manager)
        """
        self.config_dir = config_dir or (Path.home() / ".config" / "agent-manager")
        self.config_file = self.config_dir / "config.json"

    def load(self) -> AppConfig:
        """
        Load config from disk, or create default.

        Returns:
            AppConfig instance
        """
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text(encoding="utf-8"))
                return AppConfig.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                # Fall back to defaults if config is corrupted
                return self._create_default()
        return self._create_default()

    def save(self, config: AppConfig) -> None:
        """
        Persist config to disk.

        Args:
            config: AppConfig to save
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(
            json.dumps(config.to_dict(), indent=2),
            encoding="utf-8",
        )

    def _create_default(self) -> AppConfig:
        """
        Create default configuration with common scan paths.

        Returns:
            Default AppConfig instance
        """
        config = AppConfig()

        # Add common development directories if they exist
        common_paths = [
            Path.home() / "Code",
            Path.home() / "Projects",
            Path.home() / "src",
            Path.home() / "dev",
            Path.home() / "repos",
        ]

        for path in common_paths:
            if path.exists() and path.is_dir():
                config.scan_paths.append(ScanPath(path=path))

        return config

    def add_scan_path(self, config: AppConfig, path: Path) -> bool:
        """
        Add a new scan path to config.

        Args:
            config: AppConfig to modify
            path: Path to add

        Returns:
            True if added, False if already exists
        """
        path = path.resolve()
        for sp in config.scan_paths:
            if sp.path.resolve() == path:
                return False

        config.scan_paths.append(ScanPath(path=path))
        return True

    def remove_scan_path(self, config: AppConfig, path: Path) -> bool:
        """
        Remove a scan path from config.

        Args:
            config: AppConfig to modify
            path: Path to remove

        Returns:
            True if removed, False if not found
        """
        path = path.resolve()
        for i, sp in enumerate(config.scan_paths):
            if sp.path.resolve() == path:
                config.scan_paths.pop(i)
                return True
        return False
