#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_TARGETS = ("claude", "codex", "gemini")
TARGET_DIRS = {
    "claude": ".claude/skills",
    "codex": ".codex/skills",
    "gemini": ".gemini/skills",
}
SKIP_NAMES = {"__pycache__", ".DS_Store"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


@dataclass
class SyncStats:
    copied_files: int = 0
    removed_files: int = 0
    created_dirs: int = 0
    removed_dirs: int = 0
    touched_skills: set[str] = field(default_factory=set)

    def changed(self) -> bool:
        return any(
            (
                self.copied_files,
                self.removed_files,
                self.created_dirs,
                self.removed_dirs,
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync canonical skills/ into local agent skill homes.",
    )
    parser.add_argument(
        "--home",
        type=Path,
        default=Path.home(),
        help="Base home directory for target agent folders (default: current HOME)",
    )
    parser.add_argument(
        "--target",
        choices=DEFAULT_TARGETS,
        action="append",
        dest="targets",
        help="Sync only the named target; repeat to select more than one",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without modifying any target directories",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every file and directory action",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def discover_skills(skills_root: Path) -> list[Path]:
    return sorted(
        skill_dir
        for skill_dir in skills_root.iterdir()
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file()
    )


def should_skip(path: Path) -> bool:
    return path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES


def log(message: str, *, verbose: bool = True) -> None:
    if verbose:
        print(message)


def remove_path(path: Path, *, dry_run: bool, verbose: bool, stats: SyncStats) -> None:
    if path.is_dir() and not path.is_symlink():
        for child in path.iterdir():
            remove_path(child, dry_run=dry_run, verbose=verbose, stats=stats)
        log(f"remove dir  {path}", verbose=verbose)
        if not dry_run:
            path.rmdir()
        stats.removed_dirs += 1
        return

    log(f"remove      {path}", verbose=verbose)
    if not dry_run:
        path.unlink()
    stats.removed_files += 1


def ensure_directory(path: Path, *, dry_run: bool, verbose: bool, stats: SyncStats) -> None:
    if path.exists():
        if not path.is_dir():
            raise RuntimeError(f"Expected directory but found file: {path}")
        return
    log(f"mkdir       {path}", verbose=verbose)
    if not dry_run:
        path.mkdir(parents=True, exist_ok=True)
    stats.created_dirs += 1


def copy_file(source: Path, target: Path, *, dry_run: bool, verbose: bool, stats: SyncStats) -> None:
    log(f"copy        {source} -> {target}", verbose=verbose)
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    stats.copied_files += 1


def sync_entry(source: Path, target: Path, *, dry_run: bool, verbose: bool, stats: SyncStats) -> None:
    if source.is_symlink():
        raise RuntimeError(f"Symlinks inside skill directories are not supported: {source}")

    if source.is_dir():
        if target.exists() and not target.is_dir():
            raise RuntimeError(f"Cannot sync directory onto file: {target}")
        ensure_directory(target, dry_run=dry_run, verbose=verbose, stats=stats)

        source_entries = {
            entry.name: entry
            for entry in source.iterdir()
            if not should_skip(entry)
        }
        target_entries = {entry.name: entry for entry in target.iterdir()} if target.exists() else {}

        for extra_name in sorted(set(target_entries) - set(source_entries)):
            remove_path(
                target_entries[extra_name],
                dry_run=dry_run,
                verbose=verbose,
                stats=stats,
            )

        for name in sorted(source_entries):
            sync_entry(
                source_entries[name],
                target / name,
                dry_run=dry_run,
                verbose=verbose,
                stats=stats,
            )
        return

    if should_skip(source):
        return

    if target.exists() and target.is_dir():
        raise RuntimeError(f"Cannot sync file onto directory: {target}")

    if not target.exists() or not filecmp.cmp(source, target, shallow=False):
        copy_file(source, target, dry_run=dry_run, verbose=verbose, stats=stats)
        return

    source_mode = source.stat().st_mode & 0o777
    target_mode = target.stat().st_mode & 0o777
    if source_mode != target_mode:
        log(f"chmod       {target}", verbose=verbose)
        if not dry_run:
            os.chmod(target, source_mode)
        stats.copied_files += 1


def sync_skill(source_skill: Path, target_root: Path, *, dry_run: bool, verbose: bool) -> SyncStats:
    stats = SyncStats()
    target_skill = target_root / source_skill.name
    stats.touched_skills.add(source_skill.name)
    sync_entry(source_skill, target_skill, dry_run=dry_run, verbose=verbose, stats=stats)
    return stats


def merge_stats(total: SyncStats, partial: SyncStats) -> None:
    total.copied_files += partial.copied_files
    total.removed_files += partial.removed_files
    total.created_dirs += partial.created_dirs
    total.removed_dirs += partial.removed_dirs
    total.touched_skills.update(partial.touched_skills)


def main() -> int:
    args = parse_args()
    targets = args.targets or list(DEFAULT_TARGETS)
    skills_root = repo_root() / "skills"
    skills = discover_skills(skills_root)
    if not skills:
        print(f"No skills found in {skills_root}", file=sys.stderr)
        return 1

    for target_name in targets:
        target_root = args.home / TARGET_DIRS[target_name]
        total = SyncStats()
        print(f"[sync] {target_name}: {target_root}")
        if not args.dry_run:
            target_root.mkdir(parents=True, exist_ok=True)
        for skill in skills:
            partial = sync_skill(
                skill,
                target_root,
                dry_run=args.dry_run,
                verbose=args.verbose,
            )
            merge_stats(total, partial)
        if total.changed():
            print(
                f"  updated {len(total.touched_skills)} skills "
                f"(copied={total.copied_files}, removed_files={total.removed_files}, "
                f"created_dirs={total.created_dirs}, removed_dirs={total.removed_dirs})"
            )
        else:
            print(f"  already in sync across {len(total.touched_skills)} skills")

    return 0


if __name__ == "__main__":
    sys.exit(main())
