"""Schema validation for agent configurations."""

import json
from pathlib import Path
from typing import Any

import jsonschema


class AgentValidator:
    """Validates agent configurations against schema."""

    def __init__(self, schema_path: Path | None = None):
        """
        Initialize validator.

        Args:
            schema_path: Path to schema.json (default: auto-detect)
        """
        self.schema_path = schema_path or self._find_schema()
        self.schema = self._load_schema()

    def _find_schema(self) -> Path:
        """Find schema.json in common locations."""
        # Check current package directory
        pkg_dir = Path(__file__).parent.parent.parent.parent
        schema = pkg_dir / "schema.json"
        if schema.exists():
            return schema

        # Check common locations
        candidates = [
            Path.home() / ".claude" / "schema.json",
            Path("/usr/share/agent-manager/schema.json"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        raise FileNotFoundError("Could not find schema.json")

    def _load_schema(self) -> dict[str, Any]:
        """Load schema from file."""
        return json.loads(self.schema_path.read_text(encoding="utf-8"))

    def validate(self, data: dict[str, Any]) -> list[str]:
        """
        Validate agent data against schema.

        Args:
            data: Agent data dictionary (frontmatter + prompt)

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        try:
            jsonschema.validate(data, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(str(e.message))
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")
        return errors

    def validate_agent(
        self,
        frontmatter: dict[str, Any],
        prompt: str,
    ) -> list[str]:
        """
        Validate parsed agent components.

        Args:
            frontmatter: Parsed YAML frontmatter
            prompt: Body content (system prompt)

        Returns:
            List of validation error messages
        """
        data = {**frontmatter, "prompt": prompt}
        return self.validate(data)

    def is_valid(self, data: dict[str, Any]) -> bool:
        """
        Check if agent data is valid.

        Args:
            data: Agent data dictionary

        Returns:
            True if valid
        """
        return len(self.validate(data)) == 0
