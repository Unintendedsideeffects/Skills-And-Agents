# Obsidian CLI Reference

This is a compact repo-local reference for the official `obsidian` CLI. Use it when the skill needs quick reminders for common command groups without depending on upstream runtime content.

## Basics

```bash
obsidian <command> [subcommand] [key=value ...] [flags]
obsidian "Vault Name" <command> ...
```

- Arguments use `key=value`
- Use quotes for values with spaces
- Paths are vault-relative
- The Obsidian desktop app must be running

## High-Value Commands

### Notes

```bash
obsidian read path="Folder/Note.md"
obsidian create path="Folder/New Note" content="# Title"
obsidian append path="Folder/Note.md" content="extra line"
obsidian prepend path="Folder/Note.md" content="header"
obsidian move path="Folder/Old.md" to="Archive/Old.md"
obsidian rename path="Folder/Old.md" to="New.md"
obsidian delete path="Folder/Old.md"
obsidian files
obsidian folders
```

### Daily Notes

```bash
obsidian daily
obsidian daily:read
obsidian daily:append content="- [ ] Task"
obsidian daily:prepend content="## Notes"
obsidian daily:path
```

### Search

```bash
obsidian search query="term"
obsidian search query="term" path="Work" limit=10
obsidian search query="term" format=json
obsidian search:context query="term"
```

### Properties and Tags

```bash
obsidian properties path="Note.md"
obsidian property:read path="Note.md" name="status"
obsidian property:set path="Note.md" name="status" value="active"
obsidian property:remove path="Note.md" name="status"
obsidian tags
obsidian tags counts sort=count
obsidian tag name="project/alpha"
```

### Tasks and Links

```bash
obsidian tasks
obsidian tasks done
obsidian tasks daily
obsidian task path="Note.md" line=12 toggle
obsidian backlinks path="Note.md"
obsidian links path="Note.md"
obsidian unresolved
obsidian orphans
obsidian deadends
```

### Plugins, Themes, Snippets

```bash
obsidian plugins filter=community
obsidian plugins:enabled filter=community
obsidian plugin id=obsidian-git
obsidian plugin:install id=obsidian-git enable
obsidian plugin:enable id=obsidian-git filter=community
obsidian plugin:disable id=obsidian-git filter=community
obsidian plugin:uninstall id=obsidian-git
obsidian plugins:restrict on
obsidian plugins:restrict off

obsidian themes
obsidian theme:set name="Minimal"
obsidian theme:install name="Minimal" enable

obsidian snippets
obsidian snippets:enabled
obsidian snippet:enable name="my-snippet.css"
obsidian snippet:disable name="my-snippet.css"
```

### Sync and History

```bash
obsidian sync:status
obsidian sync:history path="Note.md"
obsidian sync:read path="Note.md" version=3
obsidian sync:restore path="Note.md" version=3
obsidian sync:deleted

obsidian history path="Note.md"
obsidian history:list path="Note.md"
obsidian history:read path="Note.md" version=2
obsidian history:restore path="Note.md" version=2
```

### Commands and Workspace

```bash
obsidian commands
obsidian command id="graph:open"
obsidian hotkeys
obsidian workspace
obsidian tabs
obsidian tab:open file="Projects/Plan.md"
```

### Dev and Automation

```bash
obsidian eval code="app.vault.getFiles().length"
obsidian dev:debug on
obsidian dev:console limit=20
obsidian dev:errors
obsidian dev:screenshot path="Attachments/debug.png"
```

## Notes

- `create` usually takes a path without the `.md` suffix
- `move` targets should include the destination filename
- `format=json` is useful for machine parsing on supported commands
- If the CLI emits wrapper noise, verify outcome with a focused follow-up command
