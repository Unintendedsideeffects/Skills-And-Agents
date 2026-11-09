# AI agents: always launch in a dedicated tmux session, so an SSH drop never
# kills them (same convention as PCT 103's ~/.dotfiles/cli/aliases).
# Already inside tmux -> run in place. Detach: Ctrl-b d. Reattach: agents / tmux attach -t <name>.
# Interactive shells only: scripts and `sudo codex exec ...` are unaffected.
_agent_tmux() {
    local name="$1"; shift
    if [ -n "$TMUX" ] || ! command -v tmux >/dev/null 2>&1; then
        command "$@"
    else
        TMUX= tmux new-session -s "agent-${name}-$(date +%Y%m%d-%H%M%S)" -c "$PWD" -- "$@"
    fi
}
claude() { _agent_tmux claude claude "$@"; }
codex()  { _agent_tmux codex codex "$@"; }
agy()    { _agent_tmux agy agy "$@"; }
gemini() { agy "$@"; }
# List agent sessions, or attach to one: `agents` / `agents <name>`
agents() {
    if [ -n "$1" ]; then tmux attach -t "$1"
    else tmux ls 2>/dev/null | grep '^agent-' || echo "no agent sessions"; fi
}
