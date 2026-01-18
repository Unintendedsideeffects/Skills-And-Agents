"""YAML frontmatter parser for agent and skill files."""

from pathlib import Path
from typing import Any

import yaml


class FrontmatterParser:
    """Parse YAML frontmatter from markdown files."""

    def parse(self, file_path: Path) -> tuple[dict[str, Any], str]:
        """
        Parse a markdown file with YAML frontmatter.

        Args:
            file_path: Path to the markdown file

        Returns:
            Tuple of (frontmatter_dict, body_content)

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        content = file_path.read_text(encoding="utf-8")
        return self.parse_string(content, file_path.name)

    def parse_string(
        self, content: str, filename: str = "<string>"
    ) -> tuple[dict[str, Any], str]:
        """
        Parse a string with YAML frontmatter.

        Args:
            content: String content to parse
            filename: Name for error messages

        Returns:
            Tuple of (frontmatter_dict, body_content)

        Raises:
            ValueError: If format is invalid
        """
        content = content.strip()

        if not content.startswith("---"):
            raise ValueError(f"No frontmatter found in {filename}")

        # Split on --- delimiter
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid frontmatter format in {filename}")

        frontmatter_str = parts[1].strip()
        body = parts[2].strip()

        if not frontmatter_str:
            raise ValueError(f"Empty frontmatter in {filename}")

        try:
            frontmatter = yaml.safe_load(frontmatter_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {filename}: {e}") from e

        if not isinstance(frontmatter, dict):
            raise ValueError(f"Frontmatter must be a dictionary in {filename}")

        return frontmatter, body

    def serialize(self, frontmatter: dict[str, Any], body: str) -> str:
        """
        Serialize frontmatter and body back to markdown format.

        Args:
            frontmatter: Dictionary of frontmatter fields
            body: Body content

        Returns:
            Complete markdown string with frontmatter
        """
        # Use default_flow_style=False for readable YAML
        frontmatter_str = yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        ).strip()

        return f"---\n{frontmatter_str}\n---\n\n{body}\n"
