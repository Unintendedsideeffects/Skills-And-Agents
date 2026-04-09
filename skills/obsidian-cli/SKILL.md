---
name: obsidian-cli
description: Use when the user wants direct terminal-driven interaction with a live Obsidian vault through the official Obsidian CLI. Covers concrete vault operations such as note CRUD, daily-note workflows, vault search, tasks, links, plugin management, and sync/history checks performed against a running Obsidian desktop app.
---

# Obsidian CLI

Use the official `obsidian` CLI to act on a running Obsidian desktop instance instead of manipulating vault files blindly on disk.

## Use This Skill When

- The user wants you to read, create, append to, prepend to, rename, move, or delete notes in Obsidian
- The user wants daily-note operations such as reading today's note or appending a log entry
- The user wants vault search, backlinks, orphan/dead-end checks, unresolved links, tags, properties, or task queries
- The user wants plugin, theme, snippet, sync, history, workspace, or command execution through Obsidian itself
- The user wants terminal automation against a live vault rather than a markdown-only filesystem edit

## Do Not Use This Skill When

- The user only wants conceptual advice about Obsidian, plugins, themes, or workflows
- The task is just markdown authoring or note-organization work that does not need a running Obsidian instance
- The task is better handled by a note-structure or knowledge-management agent such as `obsidian-note-organizer`
- The request is purely about filesystem edits in a vault clone and there is no value in going through Obsidian itself

Use this skill when command semantics matter. Skip it when plain file edits are simpler and equally correct.

## Preconditions

1. `obsidian` must be on `PATH`
2. Obsidian Desktop must be running
3. CLI must be enabled in Obsidian settings
4. If multiple vaults exist, target the intended vault explicitly when there is any ambiguity

## Working Rules

1. Prefer the CLI over ad hoc file edits when the request is naturally a vault operation
2. Prefer explicit vault targeting when there is any chance the active vault is not the intended one
3. Use read-only inspection first when changing plugins, sync, or history state
4. If a CLI action fails, identify whether the blocker is missing PATH setup, disabled CLI, no running desktop instance, or wrong vault selection
5. When a request can be satisfied either by CLI or raw file edits, choose the CLI only if it provides safer semantics or user-visible parity with Obsidian behavior
6. Use vault-relative paths for Obsidian commands
7. Quote `key=value` arguments when values contain spaces
8. Verify results with a follow-up read/list command after writes when practical
9. If the CLI is noisy in this environment, summarize the meaningful result instead of relaying wrapper noise

## Command Shape

```bash
obsidian <command> [subcommand] [key=value ...] [flags]
```

To target a specific vault:

```bash
obsidian "Vault Name" <command> ...
```

## Common Patterns

### Read and write notes

```bash
obsidian read path="Projects/Plan.md"
obsidian create path="Projects/New Note" content="# New Note"
obsidian append path="Projects/Plan.md" content="- next item"
obsidian prepend path="Projects/Plan.md" content="## Update"
obsidian move path="Projects/Old.md" to="Archive/Old.md"
obsidian delete path="Projects/Old.md"
```

### Daily notes

```bash
obsidian daily:read
obsidian daily:append content="- [ ] Follow up"
obsidian daily:prepend content="## Morning"
```

### Search and metadata

```bash
obsidian search query="crosspoint" limit=10
obsidian search query="incident" path="Work" format=json
obsidian properties path="Projects/Plan.md"
obsidian property:set path="Projects/Plan.md" name="status" value="active"
obsidian tags counts sort=count
```

### Tasks and links

```bash
obsidian tasks
obsidian tasks daily
obsidian task path="Projects/Plan.md" line=12 toggle
obsidian backlinks path="Projects/Plan.md"
obsidian unresolved
obsidian orphans
obsidian deadends
```

### Plugins and sync

```bash
obsidian plugins filter=community
obsidian plugin:install id=obsidian-git enable
obsidian plugin:disable id=obsidian-git filter=community
obsidian plugins:restrict off
obsidian sync:status
obsidian sync:history path="Projects/Plan.md"
```

## Suggested Workflow

1. Confirm the target vault when needed
2. Inspect current state with a read/list/search command
3. Execute the minimal Obsidian CLI command that satisfies the request
4. Verify the result with a second CLI command
5. Report the meaningful outcome, not the raw wrapper noise

## Decision Boundary

- Use `obsidian-cli` for live-vault actions
- Use normal shell/file tools for plain repository edits
- Use `obsidian-note-organizer` for note design, frontmatter conventions, tagging strategy, wikilink structure, and content organization
- Use both only when the task clearly needs both structure work and live vault operations

## Troubleshooting

- If `obsidian` is missing, check `command -v obsidian`
- If commands fail silently, ensure the desktop app is running and CLI is enabled
- If the wrong vault is targeted, pass the vault name as the first argument
- If you need exact flags for a command family, read `references/command-reference.md`
