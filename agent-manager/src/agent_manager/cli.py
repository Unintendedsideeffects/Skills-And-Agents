"""CLI interface for Agent Manager."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer

from agent_manager.app import AgentManagerApp
from agent_manager.core import ConfigManager, AgentSkillScanner, SymlinkManager

app_cli = typer.Typer(
    name="agent-manager",
    help="TUI Manager for Claude Code Agents and Skills",
    no_args_is_help=True,
)


@app_cli.command(name="")
def run(
    scan_paths: Optional[list[str]] = typer.Option(
        None,
        "--scan",
        "-s",
        help="Additional paths to scan for agents/skills",
    ),
) -> None:
    """Launch the interactive TUI application."""
    app = AgentManagerApp()

    # Add extra scan paths if provided
    if scan_paths:
        for path_str in scan_paths:
            path = Path(path_str).expanduser().resolve()
            app.config_manager.add_scan_path(app.config, path)

    app.run()


@app_cli.command()
def scan(
    paths: list[str] = typer.Argument(
        ...,
        help="Paths to scan for agents/skills",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """Scan paths for agents/skills without launching TUI."""
    scanner = AgentSkillScanner()
    scan_paths = [Path(p).expanduser().resolve() for p in paths]

    async def do_scan():
        return await scanner.scan_all(scan_paths)

    result = asyncio.run(do_scan())

    if json_output:
        output = {
            "agents": [a.to_dict() for a in result.agents],
            "skills": [s.to_dict() for s in result.skills],
            "errors": [{"path": str(p), "message": m} for p, m in result.errors],
        }
        typer.echo(json.dumps(output, indent=2))
    else:
        # Pretty print
        typer.echo(f"Found {len(result.agents)} agent(s)")
        for agent in result.agents:
            typer.echo(f"  • {agent.metadata.name} ({agent.metadata.model})")

        typer.echo(f"\nFound {len(result.skills)} skill(s)")
        for skill in result.skills:
            typer.echo(f"  ◆ {skill.metadata.name}")

        if result.errors:
            typer.echo(f"\n{len(result.errors)} error(s):")
            for path, error in result.errors:
                typer.echo(f"  ✗ {path}: {error}")


@app_cli.command()
def link(
    name: str = typer.Argument(..., help="Agent or skill name to link"),
    scope: str = typer.Option(
        "global",
        "--scope",
        "-s",
        help="'global' or path to project",
    ),
    is_skill: bool = typer.Option(
        False,
        "--skill",
        help="Link a skill instead of an agent",
    ),
) -> None:
    """Link an agent or skill without launching TUI."""
    config_manager = ConfigManager()
    config = config_manager.load()
    symlink_manager = SymlinkManager(claude_dir=config.claude_dir)

    if scope == "global":
        if is_skill:
            typer.echo("Skill global linking requires a source path")
            raise typer.Exit(1)
        # For agents, we need the full path
        typer.echo("Please use the TUI to link agents")
        raise typer.Exit(1)
    else:
        typer.echo("Project linking not yet implemented via CLI")
        raise typer.Exit(1)


@app_cli.command()
def list_agents(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """List all discovered agents."""
    config_manager = ConfigManager()
    config = config_manager.load()
    scanner = AgentSkillScanner()

    enabled_paths = [sp.path for sp in config.scan_paths if sp.enabled]
    if not enabled_paths:
        typer.echo("No enabled scan paths configured")
        raise typer.Exit(1)

    async def do_scan():
        return await scanner.scan_all(enabled_paths)

    result = asyncio.run(do_scan())

    if json_output:
        output = [a.to_dict() for a in result.agents]
        typer.echo(json.dumps(output, indent=2))
    else:
        typer.echo(f"Found {len(result.agents)} agent(s):\n")
        for agent in result.agents:
            typer.echo(f"  • {agent.metadata.name:<30} {agent.metadata.model}")
            typer.echo(f"    {agent.source_path}")
            typer.echo()


@app_cli.command()
def list_skills(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """List all discovered skills."""
    config_manager = ConfigManager()
    config = config_manager.load()
    scanner = AgentSkillScanner()

    enabled_paths = [sp.path for sp in config.scan_paths if sp.enabled]
    if not enabled_paths:
        typer.echo("No enabled scan paths configured")
        raise typer.Exit(1)

    async def do_scan():
        return await scanner.scan_all(enabled_paths)

    result = asyncio.run(do_scan())

    if json_output:
        output = [s.to_dict() for s in result.skills]
        typer.echo(json.dumps(output, indent=2))
    else:
        typer.echo(f"Found {len(result.skills)} skill(s):\n")
        for skill in result.skills:
            typer.echo(f"  ◆ {skill.metadata.name:<30} ({len(skill.scripts)} scripts)")
            typer.echo(f"    {skill.source_dir}")
            typer.echo()


@app_cli.command()
def config_show() -> None:
    """Show current configuration."""
    config_manager = ConfigManager()
    config = config_manager.load()

    typer.echo("Agent Manager Configuration\n")
    typer.echo(f"Config directory: {config.config_dir}")
    typer.echo(f"Claude directory: {config.claude_dir}\n")

    typer.echo("Scan Paths:")
    for sp in config.scan_paths:
        status = "✓" if sp.enabled else "✗"
        typer.echo(f"  {status} {sp.path}")
        if sp.agent_count or sp.skill_count:
            typer.echo(f"     {sp.agent_count} agents, {sp.skill_count} skills")

    if not config.scan_paths:
        typer.echo("  (none configured)")


def main():
    """Main entry point for CLI."""
    try:
        app_cli()
    except KeyboardInterrupt:
        typer.echo("\nCancelled")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
