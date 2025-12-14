#!/usr/bin/env bash
set -e

# AI Agents Installation Script
# Symlinks agent configurations to ~/.claude/agents/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_SOURCE="$SCRIPT_DIR/agents"
CLAUDE_AGENTS_DIR="$HOME/.claude/agents"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}➜${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Install agent configurations by symlinking to ~/.claude/agents/

OPTIONS:
    install [agent-names...|all]    Install specific agents (or all if none specified or "all")
    uninstall [agent-names...]  Remove specific agents (or all if none specified)
    list                        List available agents
    status                      Show installation status
    -h, --help                  Show this help message

EXAMPLES:
    $0 install                           # Install all agents
    $0 install all                       # Install all agents (explicit)
    $0 install sre-code-reviewer         # Install specific agent
    $0 uninstall obsidian-note-organizer # Remove specific agent
    $0 list                              # Show available agents
    $0 status                            # Check what's installed

EOF
}

list_agents() {
    print_info "Available agents in $AGENTS_SOURCE:"
    echo ""
    for agent in "$AGENTS_SOURCE"/*.md; do
        if [ -f "$agent" ]; then
            basename=$(basename "$agent")
            name=$(grep -m1 "^name:" "$agent" | cut -d':' -f2- | xargs)
            echo "  • $basename"
            echo "    Name: $name"
        fi
    done
}

show_status() {
    print_info "Installation status:"
    echo ""

    if [ ! -d "$CLAUDE_AGENTS_DIR" ]; then
        print_warning "Directory $CLAUDE_AGENTS_DIR does not exist"
        return
    fi

    for agent in "$AGENTS_SOURCE"/*.md; do
        if [ -f "$agent" ]; then
            basename=$(basename "$agent")
            target="$CLAUDE_AGENTS_DIR/$basename"

            if [ -L "$target" ]; then
                link_target=$(readlink "$target")
                if [ "$link_target" = "$agent" ]; then
                    echo -e "  ${GREEN}✓${NC} $basename (linked)"
                else
                    echo -e "  ${YELLOW}⚠${NC} $basename (linked to different source: $link_target)"
                fi
            elif [ -f "$target" ]; then
                echo -e "  ${YELLOW}⚠${NC} $basename (regular file, not symlink)"
            else
                echo -e "  ${RED}✗${NC} $basename (not installed)"
            fi
        fi
    done
}

install_agent() {
    local agent_file="$1"
    local basename=$(basename "$agent_file")
    local target="$CLAUDE_AGENTS_DIR/$basename"

    # Check if target exists
    if [ -L "$target" ]; then
        local link_target=$(readlink "$target")
        if [ "$link_target" = "$agent_file" ]; then
            print_warning "$basename already installed"
            return 0
        else
            print_warning "$basename is linked to different source, removing old link"
            rm "$target"
        fi
    elif [ -f "$target" ]; then
        print_error "$basename exists as regular file (not symlink)"
        read -p "Backup and replace? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mv "$target" "$target.backup.$(date +%s)"
            print_info "Backed up to $target.backup.*"
        else
            print_warning "Skipping $basename"
            return 1
        fi
    fi

    # Create symlink
    ln -s "$agent_file" "$target"
    print_info "Installed $basename"
}

uninstall_agent() {
    local agent_name="$1"
    local target="$CLAUDE_AGENTS_DIR/$agent_name"

    if [ -L "$target" ]; then
        rm "$target"
        print_info "Removed $agent_name"
    elif [ -f "$target" ]; then
        print_warning "$agent_name exists but is not a symlink (not managed by this script)"
    else
        print_warning "$agent_name not installed"
    fi
}

cmd_install() {
    # Create directory if it doesn't exist
    if [ ! -d "$CLAUDE_AGENTS_DIR" ]; then
        print_info "Creating $CLAUDE_AGENTS_DIR"
        mkdir -p "$CLAUDE_AGENTS_DIR"
    fi

    local install_all_requested=false
    for agent_name in "$@"; do
        local normalized
        normalized=$(printf '%s' "$agent_name" | tr '[:upper:]' '[:lower:]')
        if [ "$normalized" = "all" ]; then
            install_all_requested=true
            break
        fi
    done

    if [ $# -eq 0 ] || [ "$install_all_requested" = true ]; then
        if [ "$install_all_requested" = true ] && [ $# -gt 1 ]; then
            print_warning "\"all\" specified; installing all agents and ignoring other arguments"
        fi

        print_info "Installing all agents to $CLAUDE_AGENTS_DIR"
        echo ""
        for agent in "$AGENTS_SOURCE"/*.md; do
            if [ -f "$agent" ]; then
                install_agent "$agent"
            fi
        done
    else
        # Install specific agents
        print_info "Installing specified agents to $CLAUDE_AGENTS_DIR"
        echo ""
        for agent_name in "$@"; do
            # Add .md extension if not present
            [[ "$agent_name" != *.md ]] && agent_name="${agent_name}.md"

            agent_path="$AGENTS_SOURCE/$agent_name"
            if [ -f "$agent_path" ]; then
                install_agent "$agent_path"
            else
                print_error "Agent not found: $agent_name"
            fi
        done
    fi

    echo ""
    print_info "Installation complete! Run '$0 status' to verify."
}

cmd_uninstall() {
    if [ ! -d "$CLAUDE_AGENTS_DIR" ]; then
        print_warning "Directory $CLAUDE_AGENTS_DIR does not exist"
        return
    fi

    if [ $# -eq 0 ]; then
        # Uninstall all agents
        print_warning "This will remove ALL agent symlinks from $CLAUDE_AGENTS_DIR"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cancelled"
            return
        fi

        echo ""
        for agent in "$AGENTS_SOURCE"/*.md; do
            if [ -f "$agent" ]; then
                uninstall_agent "$(basename "$agent")"
            fi
        done
    else
        # Uninstall specific agents
        echo ""
        for agent_name in "$@"; do
            # Add .md extension if not present
            [[ "$agent_name" != *.md ]] && agent_name="${agent_name}.md"
            uninstall_agent "$agent_name"
        done
    fi

    echo ""
    print_info "Uninstallation complete!"
}

# Main command processing
case "${1:-}" in
    install)
        shift
        cmd_install "$@"
        ;;
    uninstall)
        shift
        cmd_uninstall "$@"
        ;;
    list)
        list_agents
        ;;
    status)
        show_status
        ;;
    -h|--help|help)
        print_usage
        ;;
    "")
        print_error "No command specified"
        echo ""
        print_usage
        exit 1
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        print_usage
        exit 1
        ;;
esac
