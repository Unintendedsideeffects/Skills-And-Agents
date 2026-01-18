#!/usr/bin/env python3

import os
import sys
from pathlib import Path

def main():
    print("Claude Agents Symlink Creator")
    print("=" * 30)
    print("1. Home (~/.claude/agents/)")
    print("2. Specific folder")
    print()
    
    while True:
        choice = input("Select option (1-2, q to quit): ").strip().lower()
        
        if choice == 'q' or choice == 'quit':
            print("Goodbye!")
            sys.exit(0)
        elif choice == '1':
            create_home_symlink()
            break
        elif choice == '2':
            create_folder_symlink()
            break
        else:
            print("Invalid choice. Please enter 1, 2, or q.")

def create_home_symlink():
    home_dir = Path.home()
    target_dir = home_dir / ".claude" / "agents"
    current_dir = Path.cwd()
    
    print(f"\nCreating symlink from {current_dir} to {target_dir}")
    
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create symlink
    symlink_path = target_dir / current_dir.name
    
    if symlink_path.exists() or symlink_path.is_symlink():
        overwrite = input(f"Symlink {symlink_path} already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite == 'y' or overwrite == 'yes':
            if symlink_path.is_symlink():
                symlink_path.unlink()
            else:
                print(f"Error: {symlink_path} exists but is not a symlink")
                return
        else:
            print("Aborted.")
            return
    
    try:
        symlink_path.symlink_to(current_dir)
        print(f"✓ Symlink created: {symlink_path} -> {current_dir}")
    except Exception as e:
        print(f"Error creating symlink: {e}")

def create_folder_symlink():
    folder_path = input("Enter folder path: ").strip()
    
    if not folder_path:
        print("No folder path provided.")
        return
    
    folder_path = Path(folder_path).expanduser().resolve()
    
    if not folder_path.exists():
        create_folder = input(f"Folder {folder_path} doesn't exist. Create it? (y/n): ").strip().lower()
        if create_folder == 'y' or create_folder == 'yes':
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error creating folder: {e}")
                return
        else:
            print("Aborted.")
            return
    
    target_dir = folder_path / ".claude" / "agents"
    current_dir = Path.cwd()
    
    print(f"\nCreating symlink from {current_dir} to {target_dir}")
    
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create symlink
    symlink_path = target_dir / current_dir.name
    
    if symlink_path.exists() or symlink_path.is_symlink():
        overwrite = input(f"Symlink {symlink_path} already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite == 'y' or overwrite == 'yes':
            if symlink_path.is_symlink():
                symlink_path.unlink()
            else:
                print(f"Error: {symlink_path} exists but is not a symlink")
                return
        else:
            print("Aborted.")
            return
    
    try:
        symlink_path.symlink_to(current_dir)
        print(f"✓ Symlink created: {symlink_path} -> {current_dir}")
    except Exception as e:
        print(f"Error creating symlink: {e}")

if __name__ == "__main__":
    main()