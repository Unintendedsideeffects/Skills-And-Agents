# Agent Manager - TUI for Claude Code Agents & Skills

A beautiful, Claude Code-inspired Terminal User Interface (TUI) for discovering, configuring, and managing Claude Code agents and skills across multiple repositories.

## Features

### 🎨 Modern TUI Interface
- Dark theme inspired by Claude Code
- Vim key bindings (j/k for navigation)
- Responsive, async-first architecture
- Rich markdown preview with syntax highlighting

### 🔍 Smart Discovery
- Recursively scan directories for `.claude/agents/` and `.claude/skills/`
- Also detects standalone `agents/` and `skills/` folders
- Supports multiple scan paths simultaneously
- Async scanning for large codebases

### 🔗 Symlink Management
- Link agents globally (`~/.claude/agents/`) or per-project
- Link skills globally (`~/.claude/skills/`) or per-project
- View current link status for each agent/skill
- Conflict detection and error handling

### 📋 Configuration
- Persistent config in `~/.config/agent-manager/`
- Manage scan paths from within the TUI
- Track metadata (agent count, last scan time)
- XDG-compliant storage

### 💻 CLI & TUI Modes
- Interactive TUI for visual management
- CLI commands for automation and scripts
- JSON output for integration with other tools

## Installation

### Prerequisites
- Python 3.10+
- pip or pipx

### From Source

Clone and install in development mode:

```bash
cd /home/malcolm/Code/Agents
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Activate Command

After installation, you can run:

```bash
agent-manager        # Launch the TUI (no args needed)
```

Or with the venv:

```bash
source venv/bin/activate
agent-manager
```

## Quick Start

### 1. Launch the TUI

```bash
agent-manager
```

You'll see the Dashboard with overview statistics.

### 2. Add Scan Paths (First Time)

Press `,` to go to Settings and add directories to scan:
- `~/Code` - Scan your code directory
- `~/Projects` - Scan your projects
- Any path with `.claude/agents` or `agents/` folders

### 3. Scan for Agents & Skills

Press `r` to refresh and discover all agents and skills.

### 4. Browse & Link

- Press `a` to view agents
- Press `s` to view skills
- Use `j`/`k` to navigate
- Press `/` to search
- Press `g` to link globally
- Press `u` to unlink

## Key Bindings

| Key | Action | Screen |
|-----|--------|--------|
| `d` | Dashboard | All |
| `a` | Agents | All |
| `s` | Skills | All |
| `,` | Settings | All |
| `j` | Down | Lists |
| `k` | Up | Lists |
| `g` | Link globally | Agents/Skills |
| `p` | Link to project | Agents/Skills (planned) |
| `u` | Unlink | Agents/Skills |
| `/` | Search/filter | Lists |
| `r` | Refresh scan | Dashboard/Lists |
| `q` | Quit | All |
| `Escape` | Clear search | Lists |

## Screens

### Dashboard
Overview of your agent/skill library:
- Total agents and skills discovered
- Global linked count
- Number of configured scan paths
- Quick navigation to other screens

### Agents Screen
List and manage agents:
- Search agents by name or description
- Preview selected agent (description, model, prompt)
- View current link status
- Link/unlink agents globally
- See metadata (model, color, tags)

### Skills Screen
Manage skills (similar to Agents):
- List all discovered skills
- Preview skill content
- Search and filter
- Link/unlink skills

### Settings Screen
Configure the application:
- Add/remove scan paths
- Toggle paths enabled/disabled
- View configuration directory paths
- Save configuration

## CLI Commands

### Launch TUI
```bash
agent-manager
agent-manager --scan ~/ExtraProjects
```

### List Agents
```bash
agent-manager list-agents              # Pretty print
agent-manager list-agents --json       # JSON output
```

### List Skills
```bash
agent-manager list-skills
agent-manager list-skills --json
```

### Scan Paths
```bash
agent-manager scan ~/Code ~/Projects
agent-manager scan ~/Code --json       # JSON output
```

### View Configuration
```bash
agent-manager config-show
```

## File Organization

Your agents and skills should be organized in one of these patterns:

### Pattern 1: Project-Embedded (Recommended)
```
my-project/
├── .claude/
│   ├── agents/
│   │   ├── my-agent.md
│   │   └── another-agent.md
│   └── skills/
│       └── my-skill/
│           ├── SKILL.md
│           └── scripts/
└── ...
```

### Pattern 2: Standalone Repo
```
my-agents-repo/
├── agents/
│   ├── agent1.md
│   └── agent2.md
├── skills/
│   ├── skill1/
│   │   ├── SKILL.md
│   │   └── scripts/
│   └── skill2/
│       └── SKILL.md
└── ...
```

## Agent File Format

Agents are markdown files with YAML frontmatter:

```yaml
---
name: my-awesome-agent
description: "Detailed description of what this agent does. Used for search and help. (50+ chars)"
model: sonnet
color: blue
tags: [code-review, python]
version: 1.0.0
author: Your Name
tools: [bash, read, write]
---

# Agent System Prompt

This is the actual system prompt that defines the agent's behavior...
Long description of expertise, output format, behavior patterns, etc.
```

**Required Fields:**
- `name` - kebab-case identifier
- `description` - 50+ character description
- `model` - sonnet, opus, haiku, gpt-4, gpt-3.5-turbo
- `prompt` - Body content (the system prompt)

**Optional Fields:**
- `color` - UI color: red, orange, yellow, green, blue, purple, pink, gray
- `tags` - Array of tags for categorization
- `version` - Semantic version (1.0.0)
- `author` - Author name
- `tools` - Array of required tools

## Skill File Format

Skills are directories with a `SKILL.md` file:

```
my-skill/
├── SKILL.md
└── scripts/
    ├── main.sh
    └── helper.py
```

**SKILL.md Format:**
```yaml
---
name: my-skill-name
description: What this skill does
---

# Skill Content

Implementation details, usage instructions, etc.
```

## Configuration

Config is stored in `~/.config/agent-manager/config.json`:

```json
{
  "scan_paths": [
    {
      "path": "/home/user/Code",
      "enabled": true,
      "agent_count": 12,
      "skill_count": 3
    }
  ],
  "global_agents": ["sre-code-reviewer", "ast-grep-developer"],
  "global_skills": ["obsidian2epub"],
  "theme": "dark",
  "vim_mode": true,
  "show_preview": true,
  "preview_width": 50
}
```

## Architecture

### Core Modules

- **`models/`** - Data models (Agent, Skill, Config)
- **`core/`** - Business logic
  - `scanner.py` - Recursive filesystem scanning
  - `parser.py` - YAML frontmatter parsing
  - `symlink_manager.py` - Create/remove symlinks
  - `config_manager.py` - Config persistence
  - `validator.py` - Schema validation
- **`ui/`** - Textual components
  - `screens/` - Main screens (Dashboard, Agents, Skills, Settings)
  - `widgets/` - Reusable widgets (ListItem, PreviewPane, StatCard)
  - `styles/theme.tcss` - CSS theme

### Data Flow

```
1. User launches: agent-manager
2. App loads config from ~/.config/agent-manager/
3. Scanner async-scans configured paths
4. Parser extracts frontmatter from .md files
5. SymlinkManager checks link status
6. Results populate TUI screens
7. User navigates, searches, links agents/skills
8. Config persisted on changes
```

## Advanced Usage

### Custom Scan Paths

Add a path dynamically when launching:

```bash
agent-manager --scan ~/my-agents-repo
```

### Scripting with CLI

Get JSON output for integration:

```bash
# Get all agents as JSON
agents=$(agent-manager list-agents --json)

# Filter by model
agents | jq '.[] | select(.model == "opus")'

# Check link status
agents | jq '.[] | select(.link_status == "unlinked")'
```

### Batch Operations

Find all unlinked agents from a specific repo:

```bash
agent-manager scan ~/my-repo --json | \
  jq '.agents[] | select(.link_status == "unlinked") | .name'
```

## Development

### Project Structure

```
src/agent_manager/
├── __init__.py
├── __main__.py         # Entry point for python -m
├── app.py              # Main Textual App
├── cli.py              # CLI commands
├── models/             # Data models
├── core/               # Business logic
└── ui/                 # UI components
```

### Dependencies

Core:
- `textual` >= 0.75.0 - TUI framework
- `pyyaml` >= 6.0 - YAML parsing
- `pydantic` >= 2.0 - Data validation
- `jsonschema` >= 4.0 - Schema validation
- `typer` >= 0.9.0 - CLI commands
- `rich` >= 13.0 - Terminal formatting

Dev:
- `pytest` - Testing
- `pytest-asyncio` - Async test support
- `textual-dev` - Textual development tools

### Running Tests

```bash
source venv/bin/activate
pytest tests/
```

### Running in Development

```bash
source venv/bin/activate
python -m agent_manager
```

Or with live reloading (requires textual-dev):

```bash
textual run --dev agent_manager.app:AgentManagerApp
```

## Troubleshooting

### No agents/skills found

1. Check scan paths: `agent-manager config-show`
2. Add correct paths: Press `,` in Settings
3. Verify file structure: Look for `.claude/agents/*.md` or `agents/*.md`
4. Refresh: Press `r` or restart the app

### Permission errors

- Ensure you have read access to the target directories
- The `~/.claude/` directory may need to be created first
- Try `mkdir -p ~/.claude/{agents,skills}`

### UI rendering issues

- Update Textual: `pip install --upgrade textual`
- Check terminal size (minimum 80x24)
- Disable graphics: Set `TERM=xterm-256color`

## Contributing

Improvements and fixes are welcome! Common contributions:

- Additional screens (e.g., edit agent metadata)
- Project assignment UI
- More CLI commands
- Better error messages
- Tests

## License

MIT - Same as the parent Agents project

## Related

- [Agent Repository](README.md) - Parent project with agent definitions
- [Claude Code](https://github.com/anthropics/claude-code) - Official Anthropic CLI
- [Textual](https://textual.textualize.io/) - Modern TUI framework

## Roadmap

- [ ] Edit agent/skill metadata in TUI
- [ ] Project-specific linking UI
- [ ] Agent/skill templates for creation
- [ ] Watch mode (auto-detect file changes)
- [ ] Export to Claude Code config
- [ ] Multi-user support
- [ ] Agent usage analytics
- [ ] Integration with Claude API for validation
