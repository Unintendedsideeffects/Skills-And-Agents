# AI Agents

A curated collection of specialized AI agent configurations for building powerful, context-aware AI tooling. Each agent is a carefully crafted system prompt designed to give AI assistants specific expertise and consistent behavior patterns.

## What Are These Agents?

Think of agents as "expert modes" for AI assistants. Instead of a general-purpose AI, you get a specialized expert - an SRE reviewing your infrastructure, a product owner prioritizing features, or an Obsidian expert organizing your notes.

Each agent configuration includes:
- **Expertise definition** - What the agent knows and how it thinks
- **Response patterns** - Consistent output formats and behaviors
- **Usage examples** - When and how to invoke the agent
- **Model preferences** - Recommended AI model for best results

## Quick Start

### Installation

Clone this repository and use the install script to symlink agents to your `~/.claude/agents/` directory:

```bash
# Clone the repository
git clone https://github.com/yourusername/agents.git
cd agents

# Install all agents
./install.sh install

# Or install specific agents
./install.sh install sre-code-reviewer project-owner-advisor

# Check installation status
./install.sh status

# List available agents
./install.sh list
```

The install script creates symlinks, so when you `git pull` updates, your agents automatically stay current!

**Uninstall:**
```bash
# Remove all agents
./install.sh uninstall

# Remove specific agents
./install.sh uninstall obsidian-note-organizer
```

### Using Agents in Your CLI Tool

```python
# Example: Load and use an agent configuration
import yaml
from pathlib import Path

def load_agent(agent_name: str) -> dict:
    """Load an agent configuration from the agents directory"""
    agent_path = Path(f"agents/{agent_name}.md")

    # Parse frontmatter and content
    content = agent_path.read_text()
    parts = content.split('---', 2)

    frontmatter = yaml.safe_load(parts[1])
    prompt = parts[2].strip()

    return {
        **frontmatter,
        'prompt': prompt
    }

# Use the agent
sre_agent = load_agent('sre-code-reviewer')
print(f"Agent: {sre_agent['name']}")
print(f"Model: {sre_agent['model']}")

# Pass the prompt to your AI API
response = ai_client.chat(
    model=sre_agent['model'],
    system_prompt=sre_agent['prompt'],
    user_message="Review this deployment script..."
)
```

### Using with Claude Code

```bash
# Agents can be invoked as specialized task handlers
# Example: Review code with SRE expertise
claude-code --agent sre-code-reviewer review-deployment.sh

# Or organize notes with Obsidian expert
claude-code --agent obsidian-note-organizer "structure my meeting notes"
```

## Available Agents

### 🔧 SRE Code Reviewer
**File:** `agents/sre-code-reviewer.md`
**Model:** Sonnet
**Use When:** You need expert Site Reliability Engineering review of code, infrastructure, or system designs

An elite SRE with 10+ years experience running large-scale distributed systems. Provides contextually appropriate recommendations based on system criticality - strict standards for customer-facing production, pragmatic advice for internal tools.

**Focus Areas:**
- Observability (metrics, logging, tracing, alerting)
- Reliability (error handling, retries, circuit breakers)
- Performance (bottlenecks, scalability)
- Operational readiness (deployment safety, rollback)
- Incident response and capacity planning

**Best For:** Production infrastructure, deployment pipelines, monitoring systems, reliability improvements

---

### 📊 Project Owner Advisor
**File:** `agents/project-owner-advisor.md`
**Model:** Sonnet
**Use When:** You need strategic product guidance, feature prioritization, or UX/UI critique

A seasoned Product Owner embodying the intuitive wisdom of legendary producers like Rick Rubin. Cuts through complexity to identify what makes products truly great.

**Core Capabilities:**
- Feature prioritization (Critical/High/Medium/Low with justification)
- UX/UI analysis (friction points, cognitive load, consistency)
- Project direction and strategic alignment
- Direct, honest feedback focused on user value

**Best For:** Feature planning, product roadmaps, UX reviews, scope decisions, strategic direction

---

### 📝 Obsidian Note Organizer
**File:** `agents/obsidian-note-organizer.md`
**Model:** Sonnet
**Use When:** You need to create, structure, or reorganize notes in Obsidian format

An Obsidian expert with years of experience in knowledge management. Applies strict standards for consistency, discoverability, and interconnected knowledge graphs.

**Specialties:**
- YAML frontmatter with consistent metadata
- Hierarchical tagging systems (#project/meeting)
- Wikilinks, embeds, and block references
- Mermaid diagrams (flowcharts, mind maps, timelines)
- Cross-references and backlinks

**Best For:** Note creation, knowledge base organization, meeting notes, documentation structuring

---

### 🌳 AST-Grep Developer
**File:** `agents/ast-grep-developer.md`
**Model:** Sonnet
**Use When:** You need syntax-aware code search, refactoring, or transformations

A syntax-aware code transformation specialist. Always prefers AST-based operations over plain text search for safer, more precise code modifications.

**Approach:**
- AST-first workflow (never regex when AST is available)
- Safety-first with preview before apply
- Language-specific pattern expertise (Rust, Java, Python, TypeScript/JavaScript)
- Codemod generation for complex refactors
- Git-based rollback strategies

**Best For:** Code refactoring, pattern-based search/replace, API migrations, code modernization

---

## Agent Configuration Format

All agents follow a standardized format validated against `schema.json`:

```yaml
---
name: agent-name-in-kebab-case
description: Detailed description including when to use this agent and examples
model: sonnet  # or opus, haiku, gpt-4, etc.
color: blue    # UI display color
---

[Agent system prompt content follows here]
```

### Schema Validation

The repository includes a JSON schema (`schema.json`) that defines:
- Required fields: `name`, `description`, `model`, `prompt`
- Optional fields: `color`, `tags`, `version`, `author`, `tools`
- Validation rules for names, descriptions, and formats

## Integration Patterns

### Pattern 1: Direct Prompt Injection
Load the agent prompt as a system message in your AI API calls.

### Pattern 2: Agent Router
Build a router that selects agents based on user intent or command flags.

### Pattern 3: Multi-Agent Workflows
Chain multiple agents for complex tasks (e.g., code-reviewer → obsidian-note-organizer for review documentation).

### Pattern 4: Agent Marketplace
Fork this repo and add your own specialized agents for your domain.

## Project Structure

```
.
├── agents/                    # Agent configuration files
│   ├── ast-grep-developer.md
│   ├── obsidian-note-organizer.md
│   ├── project-owner-advisor.md
│   └── sre-code-reviewer.md
├── scripts/                   # Utility scripts
│   └── validate_agents.py     # Schema validation script
├── .github/
│   └── workflows/
│       └── validate-agents.yml  # CI validation
├── install.sh                 # Installation script for symlinks
├── schema.json                # JSON schema for validation
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Contributing

Want to add your own agent? Great! Here's what makes a high-quality agent:

1. **Clear expertise domain** - Focused role, not general purpose
2. **Consistent output format** - Predictable, structured responses
3. **Usage examples** - Show when and how to use it
4. **Well-tested prompts** - Validated with real use cases
5. **Schema compliance** - Validates against `schema.json`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines (coming soon).

## Validation & CI

Agent configurations are validated against the schema in CI to ensure:
- All required fields are present
- Names follow kebab-case convention
- Descriptions are detailed enough (50+ chars)
- Models are from supported list
- No additional properties beyond schema

Run validation locally:
```bash
# Validation script (requires Python 3.8+)
python scripts/validate_agents.py
```

## Philosophy

**Good agents are:**
- **Specialized** - Do one thing exceptionally well
- **Consistent** - Predictable patterns and output
- **Contextual** - Adapt recommendations to actual requirements
- **Honest** - Direct feedback over false validation

**Bad agents are:**
- Generic catch-alls trying to do everything
- Inconsistent or unpredictable in responses
- One-size-fits-all without considering context
- Overly agreeable without critical thinking

## License

MIT - Feel free to use these agents in your projects, commercial or otherwise.

## Acknowledgments

These agents are designed to work with:
- [Claude Code](https://github.com/anthropics/claude-code) - Official Anthropic CLI
- [Aider](https://github.com/paul-gauthier/aider) - AI pair programming
- [OpenAI API](https://openai.com/api/) - GPT-4 and beyond
- Any AI system that supports system prompts

Built with inspiration from the agent-based architecture patterns emerging in AI tooling.
