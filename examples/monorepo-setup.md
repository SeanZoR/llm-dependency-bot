# Monorepo Setup Guide

This guide shows how to configure LLM Dependency Bot for monorepos with multiple package managers.

## Scenario

You have a monorepo with:

- Frontend (npm/pnpm)
- Backend (pip/poetry)
- Infrastructure (Terraform)
- Multiple services

## Configuration

### 1. Basic Monorepo Setup

```yaml
name: LLM Dependency Bot

on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_run:
    workflows: ["Monorepo CI"]
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

          # Different critical deps for different parts of monorepo
          critical-dependencies: |
            react,next,vue,
            fastapi,django,flask,
            terraform,aws-cdk
```

### 2. Path-Specific Configuration

For different behavior based on path:

```yaml
jobs:
  frontend-deps:
    if: |
      github.actor == 'dependabot[bot]' &&
      contains(github.event.pull_request.title, 'frontend/')
    runs-on: ubuntu-latest
    steps:
      - uses: SeanZoR/llm-dependency-bot@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          critical-dependencies: react,next,vue

  backend-deps:
    if: |
      github.actor == 'dependabot[bot]' &&
      contains(github.event.pull_request.title, 'backend/')
    runs-on: ubuntu-latest
    steps:
      - uses: SeanZoR/llm-dependency-bot@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          critical-dependencies: fastapi,sqlalchemy,pydantic
```

### 3. Ecosystem-Specific Strategies

#### JavaScript/TypeScript

```yaml
# frontend/.github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "frontend"
```

Bot will:

- Auto-merge: Patch updates, type definitions
- Review: Minor updates, framework changes
- Block: Major updates without CI

#### Python

```yaml
# backend/.github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "backend"
```

Bot will:

- Auto-merge: Patch updates, security fixes
- Review: Minor updates, ML library changes
- Block: Major updates, framework changes

## Best Practices

### 1. Separate CI Workflows

```yaml
# .github/workflows/frontend-ci.yml
name: Frontend CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd frontend && npm test

# .github/workflows/backend-ci.yml
name: Backend CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd backend && pytest
```

### 2. Require All CI to Pass

```yaml
# .github/workflows/dependency-bot.yml
on:
  workflow_run:
    workflows: ["Frontend CI", "Backend CI", "Integration Tests"]
    types: [completed]
```

Bot only runs after ALL workflows complete.

### 3. Custom Critical Dependencies Per Path

Use matrix strategy:

```yaml
jobs:
  dependency-bot:
    strategy:
      matrix:
        include:
          - path: frontend
            critical: "react,next,vue"
          - path: backend
            critical: "fastapi,django"
          - path: infra
            critical: "terraform,pulumi"

    if: |
      github.actor == 'dependabot[bot]' &&
      contains(github.event.pull_request.title, matrix.path)

    steps:
      - uses: SeanZoR/llm-dependency-bot@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          critical-dependencies: ${{ matrix.critical }}
```

## Common Patterns

### Pattern 1: Different Merge Strategies

```yaml
# Frontend: Aggressive auto-merge
frontend-deps:
  steps:
    - uses: SeanZoR/llm-dependency-bot@v1
      with:
        auto-merge-enabled: true
        merge-method: squash

# Backend: Conservative, rebase to keep history
backend-deps:
  steps:
    - uses: SeanZoR/llm-dependency-bot@v1
      with:
        auto-merge-enabled: true
        merge-method: rebase
        critical-dependencies: fastapi,sqlalchemy,pydantic
```

### Pattern 2: Staging Environment

```yaml
jobs:
  dependency-bot-staging:
    # First, auto-merge to staging branch
    if: github.base_ref == 'staging'
    steps:
      - uses: SeanZoR/llm-dependency-bot@v1
        with:
          auto-merge-enabled: true

  dependency-bot-production:
    # Then, require review for production
    if: github.base_ref == 'main'
    steps:
      - uses: SeanZoR/llm-dependency-bot@v1
        with:
          auto-merge-enabled: false  # Always review for prod
```

### Pattern 3: Workspace Dependencies

For pnpm workspaces or Nx monorepos:

```yaml
steps:
  - name: Check if workspace root
    id: check-root
    run: |
      if [[ "${{ github.event.pull_request.title }}" == *"package.json"* ]]; then
        echo "is_root=true" >> $GITHUB_OUTPUT
      fi

  - name: Run bot (stricter for root)
    uses: SeanZoR/llm-dependency-bot@v1
    with:
      auto-merge-enabled: ${{ steps.check-root.outputs.is_root != 'true' }}
```

## Troubleshooting

### Issue: Bot merges wrong PRs

**Solution**: Use stricter conditions

```yaml
if: |
  github.actor == 'dependabot[bot]' &&
  contains(github.event.pull_request.labels.*.name, 'dependencies') &&
  startsWith(github.event.pull_request.title, 'Bump')
```

### Issue: CI workflows conflict

**Solution**: Use workflow dependencies

```yaml
on:
  workflow_run:
    workflows: ["CI"]  # Wait for CI
    types: [completed]

jobs:
  dependency-bot:
    if: github.event.workflow_run.conclusion == 'success'
```

### Issue: Different teams own different parts

**Solution**: Use CODEOWNERS

```
# .github/CODEOWNERS
/frontend/     @frontend-team
/backend/      @backend-team

# Bot only auto-merges if CODEOWNERS don't block
```

## Example: Real-World Monorepo

```yaml
name: LLM Dependency Bot

on:
  workflow_run:
    workflows: ["Full CI Suite"]
    types: [completed]

jobs:
  dependency-bot:
    if: |
      github.actor == 'dependabot[bot]' &&
      github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest

    permissions:
      contents: write
      pull-requests: write
      checks: read

    steps:
      - name: Determine criticality
        id: critical
        run: |
          TITLE="${{ github.event.pull_request.title }}"
          if [[ $TITLE == *"react"* ]] || [[ $TITLE == *"next"* ]]; then
            echo "deps=react,next,vue" >> $GITHUB_OUTPUT
          elif [[ $TITLE == *"fastapi"* ]] || [[ $TITLE == *"django"* ]]; then
            echo "deps=fastapi,django,sqlalchemy" >> $GITHUB_OUTPUT
          else
            echo "deps=" >> $GITHUB_OUTPUT
          fi

      - name: Run LLM Dependency Bot
        uses: SeanZoR/llm-dependency-bot@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          critical-dependencies: ${{ steps.critical.outputs.deps }}
          merge-method: squash

      - name: Notify team
        if: always()
        run: |
          echo "Bot completed for ${{ github.event.pull_request.title }}"
```

---

**Key Takeaways:**

1. Use path detection to apply different strategies
2. Ensure all relevant CI passes before bot runs
3. Adjust critical dependencies per service
4. Consider staging vs. production branches
5. Use CODEOWNERS for additional safety
