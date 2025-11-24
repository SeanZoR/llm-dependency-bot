# Quick Start Guide

Get your LLM Dependency Bot up and running in 5 minutes!

## Prerequisites

- GitHub repository with Dependabot or Renovate configured
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Setup Steps

### 1. Add GitHub Workflow

Create `.github/workflows/dependency-bot.yml` in your repository:

```yaml
name: LLM Dependency Bot

on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_run:
    workflows: ["CI"]  # Replace with your CI workflow name
    types: [completed]

jobs:
  dependency-bot:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest

    permissions:
      contents: write
      pull-requests: write
      checks: read

    steps:
      - uses: SeanZoR/llm-dependency-bot@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### 2. Add Anthropic API Key

1. Go to your repository on GitHub
2. Click `Settings` → `Secrets and variables` → `Actions`
3. Click `New repository secret`
4. Name: `ANTHROPIC_API_KEY`
5. Value: Your Anthropic API key
6. Click `Add secret`

### 3. Done!

The bot will now automatically:

- ✅ **Auto-merge** safe updates (patch versions, type definitions)
- 👤 **Request review** for risky updates (major versions, breaking changes)
- ❌ **Block** problematic updates (failing CI, vulnerabilities)

## What Happens Next?

When Dependabot opens a PR:

1. **Bot analyzes** PR context, CI status, dependency info
2. **Claude decides** using AI reasoning and autonomous tool use
3. **Bot acts** - merges, requests review, or blocks with explanation

Every decision includes detailed natural language reasoning!

## Example Bot Comment

```markdown
🤖 **LLM Dependency Bot**

**Decision**: ✅ Auto-merge approved
**Risk Level**: LOW

**Claude's Analysis**:
This is a patch version update for axios with all CI checks passing.
The release notes show only bug fixes with no breaking changes.
The changed files are only lock files. Safe to auto-merge.

**Context**:
- Dependency: `axios`
- Update: `1.6.0` → `1.6.1` (patch)
- CI Status: success

Merging automatically...
```

## Customization

### Make Bot More Conservative

```yaml
- uses: SeanZoR/llm-dependency-bot@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    critical-dependencies: 'react,next,fastapi,django'  # Always require review
```

### Change Merge Method

```yaml
- uses: SeanZoR/llm-dependency-bot@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    merge-method: rebase  # Options: merge, squash, rebase
```

## Monitoring

View bot activity in:

- **PR comments** - Detailed explanations for each decision
- **Commit messages** - Reasoning included in merge commits
- **GitHub Actions logs** - Full execution details

## Cost

Typical costs:

- **Per PR analysis**: $0.01 - $0.05
- **50 PRs/month**: ~$2.50/month

Compare to:

- Engineer time: $50-100/hour
- Missing security update: 🚨

## Support & Documentation

- 📖 [Full Documentation](https://github.com/SeanZoR/llm-dependency-bot)
- 🏗️ [Architecture Guide](docs/ARCHITECTURE.md) - How it works
- 🔧 [Tool Use Guide](docs/TOOL-USE-GUIDE.md) - Custom tools
- 📝 [Prompt Engineering](docs/PROMPT-ENGINEERING.md) - Customize behavior
- 🐛 [Report Issues](https://github.com/SeanZoR/llm-dependency-bot/issues)

## FAQ

**Q: Will it work with Renovate?**
A: Yes! Detects both Dependabot and Renovate PRs.

**Q: Can I test it first?**
A: Yes! Set `auto-merge-enabled: false` to start. The bot will analyze and comment without merging.

**Q: What if it makes a wrong decision?**
A: You can always override manually. All decisions are transparent with full reasoning.

**Q: Does it work with private repos?**
A: Yes! Just add the secret to your private repository.

## Next Steps

1. ✅ Set up the bot (you just did this!)
2. 📊 Monitor first few PRs
3. ⚙️ Adjust configuration based on your needs
4. 🎯 Enjoy automated dependency management!

---

**Built with ❤️ using Claude 3.5 Sonnet**

[⭐ Star on GitHub](https://github.com/SeanZoR/llm-dependency-bot) • [📖 Read Docs](https://github.com/SeanZoR/llm-dependency-bot) • [🐛 Report Issue](https://github.com/SeanZoR/llm-dependency-bot/issues)
