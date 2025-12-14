# Getting Started with Agent Manager

## Installation (1 minute)

```bash
cd /home/malcolm/Code/Agents
python -m venv venv
source venv/bin/activate
pip install -e .
```

That's it! You now have the `agent-manager` command.

## First Run (2 minutes)

```bash
agent-manager
```

You'll see the Dashboard with 4 statistics cards. The app will try to scan `~/Code` automatically.

### What You See

- **Agents**: Count of discovered agents (should show 4 from this repo)
- **Skills**: Count of discovered skills (should show 1)
- **Global**: Count of linked agents/skills (starts at 0)
- **Scan Paths**: Number of configured paths (default: ~/Code if it exists)

## Adding More Paths (1 minute)

If you want to scan additional directories:

1. Press `,` to open Settings
2. Type a path like `~/Projects` or `~/myrepos`
3. Press Enter
4. Press `r` to refresh

## Browsing Agents (2 minutes)

1. Press `a` to go to Agents screen
2. Use `j`/`k` to navigate the list (or arrow keys)
3. Press `/` to search
4. Use arrow right to see the preview pane on the right

You'll see:
- Agent name
- Model (sonnet, opus, haiku, etc.)
- Current link status (GLOBAL, PROJECT, or unlinked)

The right pane shows:
- Agent description
- System prompt preview
- Link status

## Linking an Agent (30 seconds)

1. On the Agents screen, select an agent with `j`/`k`
2. Press `g` to link globally
3. Done! It's now in `~/.claude/agents/`

You can use it with Claude Code immediately.

## Using Skills (1 minute)

Same as agents - press `s` to view skills, `g` to link.

## Command Line Interface

If you prefer not to use the TUI:

```bash
# List all agents
agent-manager list-agents

# Get JSON output for scripting
agent-manager list-agents --json

# Scan a specific directory
agent-manager scan ~/myrepo

# View configuration
agent-manager config-show
```

## Keyboard Shortcuts (Reference)

| Key | What it does |
|-----|--------------|
| `d` | Go to Dashboard |
| `a` | Go to Agents |
| `s` | Go to Skills |
| `,` | Go to Settings |
| `j` | Move down in list |
| `k` | Move up in list |
| `/` | Search (type to filter) |
| `Escape` | Clear search |
| `g` | Link selected agent/skill globally |
| `u` | Unlink selected agent/skill |
| `r` | Refresh (re-scan directories) |
| `q` | Quit the app |

## Common Tasks

### Search for an agent
1. Go to Agents (`a`)
2. Press `/` to search
3. Type the name (e.g., "sre")
4. Matches appear instantly

### Link multiple agents
1. Go to Agents (`a`)
2. Select first agent with `j`/`k`
3. Press `g` to link
4. Move to next with `j`
5. Repeat

### Check what's linked
1. Go to Agents (`a`)
2. Look at the badge on the right:
   - "GLOBAL" = linked to ~/.claude/agents/
   - "PROJECT" = linked to a project (planned)
   - Nothing = unlinked

### Add a new scan path
1. Press `,` to go to Settings
2. Type the path
3. Press Enter
4. Press `r` to scan immediately, or it will scan on next refresh

## Troubleshooting

### "No agents found"
- Make sure you added scan paths (press `,`)
- Check the paths exist: `ls ~/Code`
- Refresh with `r`

### "Permission denied when linking"
- The ~/.claude directory may not exist
- Try: `mkdir -p ~/.claude/{agents,skills}`
- Then try again

### "TUI looks broken"
- Maximize your terminal window (needs at least 80x24 characters)
- Try a different terminal (iTerm, Alacritty, GNOME Terminal all work)

### "Where are my config and linked agents?"
- Config: `~/.config/agent-manager/config.json`
- Linked agents: `~/.claude/agents/` (symlinks)
- Linked skills: `~/.claude/skills/` (symlinks)

## Real-World Example

Let's say you have agents in `~/myagents/agents/` and skills in `~/projects/.claude/skills/`:

```bash
# Launch
agent-manager

# Add first path (Settings screen, press ,)
~/myagents        # <-- Enter this, press Enter

# Add second path
~/projects        # <-- Enter this, press Enter

# Go back to Dashboard (press d)
# Press r to refresh

# Now you'll see all your agents and skills!
# Go to Agents (press a)
# Select an agent and press g to link it
```

## Next Steps

1. **Read the docs**: `AGENT_MANAGER.md` for complete reference
2. **Explore the CLI**: `agent-manager list-agents --json` for scripting
3. **Customize settings**: Add your own scan paths
4. **Link your agents**: Use `g` to make agents available globally

## Tips & Tricks

- **Preview is powerful**: The right panel shows the full system prompt. Use it to understand what each agent does.
- **Search is fast**: Press `/` and start typing - instant filtering of 100+ agents.
- **JSON export**: `agent-manager list-agents --json | jq '.[] | .model'` to find all opus agents.
- **Config is simple**: `~/.config/agent-manager/config.json` is just JSON - you can edit it directly.
- **Offline friendly**: Everything runs locally. No internet needed.

## Getting Help

- **For questions about Agent Manager**: See `AGENT_MANAGER.md`
- **For quick reference**: See `QUICKSTART.md`
- **For detailed implementation**: See `.claude/IMPLEMENTATION_SUMMARY.md`
- **For development**: Check the source code in `src/agent_manager/`

## Have Fun!

Agent Manager makes discovering and using agents a joy. No more hunting through repositories or forgetting where you saved that awesome agent!

Now go forth and organize your agents. 🚀
