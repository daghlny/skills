# Claude Code Skills

My custom Claude Code skills collection.

## Skills

| Skill | Description |
|-------|-------------|
| **render** | Renders Claude's last response as a formatted HTML page with LaTeX & code highlighting |
| **review-usage** | Analyzes Claude Code conversation history and provides improvement suggestions |

## Install on another machine

One-liner (requires `git`):

```bash
curl -fsSL https://raw.githubusercontent.com/Daghlny/skills/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/Daghlny/skills.git /tmp/skills
cp -R /tmp/skills/skills/* ~/.claude/skills/
```

## Sync local skills to this repo

When you create or update skills locally, sync them here:

```bash
./sync.sh
```

This copies all user-created skills from `~/.claude/skills/` (skipping symlinked system skills) into the `skills/` directory.
