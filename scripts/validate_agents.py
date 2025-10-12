#!/usr/bin/env python3
"""
Validate agent configuration files against the schema.

This script:
1. Loads all .md files from the agents/ directory
2. Parses YAML frontmatter and content
3. Validates against schema.json
4. Reports any validation errors
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Install with: pip install pyyaml jsonschema")
    sys.exit(1)


def parse_agent_file(file_path: Path) -> Dict:
    """Parse an agent markdown file with YAML frontmatter."""
    content = file_path.read_text(encoding='utf-8')

    # Split on --- delimiters
    parts = content.split('---', 2)

    if len(parts) < 3:
        raise ValueError(f"Invalid format: {file_path.name} must have YAML frontmatter")

    # Parse frontmatter
    frontmatter = yaml.safe_load(parts[1])
    if not frontmatter:
        raise ValueError(f"Empty frontmatter in {file_path.name}")

    # Get prompt content
    prompt = parts[2].strip()
    if not prompt:
        raise ValueError(f"Empty prompt content in {file_path.name}")

    # Combine frontmatter and prompt
    agent_data = {**frontmatter, 'prompt': prompt}

    return agent_data


def validate_agent(agent_data: Dict, schema: Dict, file_name: str) -> List[str]:
    """Validate agent data against schema and return list of errors."""
    errors = []

    # Validate against JSON schema
    validator = Draft7Validator(schema)
    for error in validator.iter_errors(agent_data):
        errors.append(f"  - {error.message} at {'.'.join(str(p) for p in error.path)}")

    return errors


def main():
    """Main validation function."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    agents_dir = repo_root / 'agents'
    schema_path = repo_root / 'schema.json'

    # Load schema
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    # Find all agent files
    if not agents_dir.exists():
        print(f"Error: Agents directory not found at {agents_dir}")
        sys.exit(1)

    agent_files = list(agents_dir.glob('*.md'))

    if not agent_files:
        print(f"Warning: No agent files found in {agents_dir}")
        sys.exit(0)

    print(f"Validating {len(agent_files)} agent(s)...")
    print()

    all_valid = True

    for agent_file in sorted(agent_files):
        try:
            # Parse agent file
            agent_data = parse_agent_file(agent_file)

            # Validate against schema
            errors = validate_agent(agent_data, schema, agent_file.name)

            if errors:
                all_valid = False
                print(f"❌ {agent_file.name}")
                for error in errors:
                    print(error)
                print()
            else:
                print(f"✅ {agent_file.name}")
                print(f"   Name: {agent_data.get('name')}")
                print(f"   Model: {agent_data.get('model')}")
                print(f"   Prompt length: {len(agent_data.get('prompt', ''))} chars")
                print()

        except Exception as e:
            all_valid = False
            print(f"❌ {agent_file.name}")
            print(f"  - Parse error: {str(e)}")
            print()

    if all_valid:
        print("✅ All agents validated successfully!")
        sys.exit(0)
    else:
        print("❌ Validation failed. Please fix the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
