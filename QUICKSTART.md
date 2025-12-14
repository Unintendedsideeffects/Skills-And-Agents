# Agent Manager - Quick Start Guide

## 5-Minute Setup

### 1. Install
```bash
cd /path/to/Agents  # Navigate to this repo
uv sync
```

### 2. First Run
```bash
uv run agent-manager
```

Or activate the environment first:
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
agent-manager
```

You'll see the Dashboard. It will try to scan `~/Code` by default.

### 3. Add Scan Paths (if needed)
- Press `,` to go to Settings
- Enter a path like `~/Code` or `~/Projects`
- Press Enter to add
- Press Ctrl+C and restart, or press `r` to refresh

### 4. Browse Your Agents & Skills
- Press `a` to see all agents
- Press `s` to see all skills
- Use `j`/`k` to navigate
- Press `/` to search
- Arrow Right to see preview

### 5. Link Agents Globally
- Select an agent
- Press `g` to link globally
- Now it's in `~/.claude/agents/`

## Key Commands at a Glance

| Press | What Happens |
|-------|--------------|
| `d` | Dashboard (overview) |
| `a` | Agents list |
| `s` | Skills list |
| `,` | Settings (add paths) |
| `j` / `k` | Move up/down |
| `/` | Search agents/skills |
| `g` | Link selected agent globally |
| `u` | Unlink selected agent |
| `r` | Refresh (re-scan) |
| `q` | Quit |

## Using the CLI

Don't want the TUI? Use the command line:

```bash
# List all agents
agent-manager list-agents

# List as JSON
agent-manager list-agents --json

# Scan a specific directory
agent-manager scan ~/myrepo

# View config
agent-manager config-show
```

## File Structure Expected

The tool looks for agents in these patterns:

```
my-repo/
├── agents/               ← or .claude/agents/
│   ├── my-agent.md
│   └── another.md
└── skills/               ← or .claude/skills/
    └── my-skill/
        ├── SKILL.md
        └── scripts/
```

If your agents are here, they'll be discovered!

## Troubleshooting

**"No agents found"**
- Check the scan path includes your agent repository
- Verify agents are in `agents/` or `.claude/agents/` folders
- Press `r` to refresh

**"Permission denied when linking"**
- The `~/.claude/` directory might not exist
- Try: `mkdir -p ~/.claude/{agents,skills}`

**"TUI looks weird"**
- Maximize your terminal window (needs at least 80x24)
- Try a different terminal (iTerm, Alacritty, GNOME Terminal work well)

## Next Steps

1. **Add more scan paths** - Settings screen (`,`)
2. **Link your favorite agents** - Agents screen (`a`) then `g`
3. **Organize your agents** - Create `.claude/agents/` in your projects
4. **Use with Claude Code** - Linked agents appear automatically

## Useful Tips

- **Search is fast** - Press `/` on any list to filter
- **Preview helps** - See agent descriptions and system prompts on the right
- **No TUI?** - Use CLI commands instead (list-agents, scan, etc.)
- **Persistent config** - Changes are saved to `~/.config/agent-manager/`
- **Works offline** - Everything runs locally, no cloud needed

Enjoy managing your agents! 🚀
