# AI agents: always launch in a dedicated tmux session, so an SSH drop never
# kills them. Session names: agent-<name>-<YYYYmmdd-HHMMSS>.
# Already inside tmux -> run in place (no nesting). Detach: Ctrl-b d.
# `agents` lists agent sessions, `agents <name>` attaches.
# Works in bash and zsh. Without a terminal (scripts, agent harness shells that
# snapshot these functions) the CLI runs directly, so `codex exec`/`agy --print`
# in a script are unaffected.
# Canonical copy: Skills-And-Agents/scripts/agent-tmux.sh

# Old alias-based setups would shadow the functions (zsh refuses to define a
# function over an alias), so clear them first.
unalias claude codex copilot agy gemini agents 2>/dev/null

_agent_tmux() {
    local name="$1"; shift
    # Run in place when already in tmux, without tmux, or without a terminal
    # (scripts, harness shells, pipes): tmux would fail with "not a terminal".
    if [ -n "$TMUX" ] || [ ! -t 0 ] || [ ! -t 1 ] || ! command -v tmux >/dev/null 2>&1; then
        command "$@"
    else
        TMUX= tmux new-session -s "agent-${name}-$(date +%Y%m%d-%H%M%S)" -c "$PWD" -- "$@"
    fi
}
claude()  { _agent_tmux claude claude "$@"; }
codex()   { _agent_tmux codex codex "$@"; }
copilot() { _agent_tmux copilot copilot "$@"; }
# agy prompts for every tool call unless told otherwise; AGY_TMUX_ARGS overrides.
agy()     { _agent_tmux agy agy ${AGY_TMUX_ARGS---dangerously-skip-permissions} "$@"; }
gemini()  { agy "$@"; }
agents() {
    if [ -n "$1" ]; then tmux attach -t "$1"
    else tmux ls 2>/dev/null | grep '^agent-' || echo "no agent sessions"; fi
}
