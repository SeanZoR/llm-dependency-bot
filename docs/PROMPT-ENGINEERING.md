# Prompt Engineering Guide

Learn how to customize Claude's behavior by modifying the system prompt and user prompts.

## The System Prompt

The system prompt defines Claude's role, capabilities, and decision framework. It's set in `src/agent.py`:

```python
AGENT_SYSTEM_PROMPT = """You are an expert dependency management agent...

Your role is to analyze dependency update pull requests and make intelligent merge decisions based on risk assessment...

**Decision Framework:**
1. AUTO_MERGE - Safe to merge immediately
2. REQUIRE_APPROVAL - Needs human review
3. DO_NOT_MERGE - Block the PR
..."""
```

## Customizing the System Prompt

### Making Claude More Conservative

**Use case**: Your team prefers human review for most updates.

```python
AGENT_SYSTEM_PROMPT = """You are a CONSERVATIVE dependency management agent.

**Core Principle**: When in doubt, always require human approval.

**Decision Framework:**

1. **AUTO_MERGE** - Only these specific cases:
   - Patch updates (x.y.Z) with passing CI
   - Type definition updates (@types/*)
   - Security patches with passing CI

2. **REQUIRE_APPROVAL** - Default for everything else:
   - ALL minor and major updates
   - Any update to critical dependencies
   - Updates with warnings in CI
   - First-time dependencies

3. **DO_NOT_MERGE**:
   - CI failures
   - Merge conflicts
   - Known vulnerabilities

**Important**: Be extremely cautious. It's better to require review than to auto-merge incorrectly.
"""
```

### Making Claude More Aggressive

**Use case**: Your team has excellent test coverage and wants fast iteration.

```python
AGENT_SYSTEM_PROMPT = """You are an AGGRESSIVE dependency management agent optimized for speed.

**Core Principle**: Trust the tests. If CI passes, it's probably safe.

**Decision Framework:**

1. **AUTO_MERGE** - Trust CI:
   - Patch updates with passing CI
   - Minor updates with passing CI (unless breaking changes explicitly mentioned)
   - Security updates (even if CI pending)
   - Dev dependencies (always, if CI passes)

2. **REQUIRE_APPROVAL** - Only for risky updates:
   - Major updates to critical dependencies (react, django, etc.)
   - Updates that modify more than lock files
   - Pre-release versions

3. **DO_NOT_MERGE**:
   - CI failures
   - Merge conflicts

**Important**: Be decisive. The comprehensive test suite will catch issues.
"""
```

### Domain-Specific Customization

**Use case**: Frontend team with specific concerns.

```python
AGENT_SYSTEM_PROMPT = """You are a dependency agent for a FRONTEND application.

**Special Concerns**:
- Bundle size impact (use check_bundle_size tool liberally)
- Browser compatibility
- React ecosystem stability
- TypeScript type safety

**Decision Framework**:

1. **AUTO_MERGE**:
   - Type definitions
   - Patch updates with passing CI and no bundle size increase
   - Security patches

2. **REQUIRE_APPROVAL**:
   - Any React/Next.js update (critical to UI)
   - Bundle size increases >10KB
   - Breaking changes to TypeScript
   - Changes to polyfills or browser support

3. **DO_NOT_MERGE**:
   - CI failures
   - Bundle size increases >50KB
   - Drops support for required browsers

**Always consider**:
- Impact on end users (performance, compatibility)
- Developer experience (TypeScript errors, API changes)
- Bundle size trade-offs
"""
```

## The User Prompt

The user prompt provides context about a specific PR:

```python
user_message = f"""Analyze this dependency update PR and decide if it should be merged:

**PR Information:**
- Title: {context.title}
- Dependency: {context.dependency_name}
- Update: {context.old_version} → {context.new_version}
- Update Type: {context.update_type}
...

Based on this information:
1. Assess the risk level
2. Make a merge decision
3. Explain your reasoning

Use tools to gather additional information if needed.
"""
```

### Enhancing the User Prompt

#### Adding Context

```python
user_message = f"""Analyze this dependency update:

**PR Information:**
{standard_context}

**Additional Context:**
- Recent incidents: {get_recent_incidents()}
- Team velocity: {get_team_velocity()}
- Deployment schedule: {get_deployment_schedule()}
- Similar PRs this week: {count_similar_prs()}

**Team Guidelines:**
- No Friday deploys
- Prefer batch updates for related packages
- Always check bundle size for frontend deps

Based on ALL this information, make your decision...
"""
```

#### Providing Examples

Few-shot prompting teaches Claude patterns:

```python
AGENT_SYSTEM_PROMPT = """...

**Example Decisions:**

Example 1:
- Update: lodash 4.17.20 → 4.17.21
- Type: Patch
- CI: Passing
- Decision: AUTO_MERGE
- Reasoning: Security patch, CI passing, well-tested library

Example 2:
- Update: react 17.0.0 → 18.0.0
- Type: Major
- CI: Passing
- Decision: REQUIRE_APPROVAL
- Reasoning: Major React update with new concurrent features, needs QA

Example 3:
- Update: axios 0.21.1 → 0.21.2
- CI: Failing (timeout on one test)
- Decision: DO_NOT_MERGE
- Reasoning: CI must pass before any merge

Now apply this pattern to the current PR...
"""
```

## Advanced Prompt Patterns

### Chain of Thought

Encourage step-by-step reasoning:

```python
user_message = f"""...

Please analyze this PR step by step:

1. **Risk Assessment**: What could go wrong?
2. **CI Analysis**: Are tests comprehensive enough?
3. **Change Scope**: What actually changed?
4. **Breaking Changes**: Any API changes?
5. **Security**: Any CVEs addressed or introduced?
6. **Performance**: Expected impact?
7. **Decision**: Based on above, what's your decision?

Think through each step before deciding.
"""
```

### Structured Output

Request specific format:

```python
user_message = f"""...

Respond EXACTLY in this JSON format:
{{
    "decision": "AUTO_MERGE|REQUIRE_APPROVAL|DO_NOT_MERGE",
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "confidence": 0.0-1.0,
    "reasoning": "Your detailed reasoning",
    "key_factors": ["factor 1", "factor 2", ...],
    "tools_used": ["tool1", "tool2"],
    "recommended_actions": ["action 1", "action 2"]
}}
"""
```

### Multi-Perspective Analysis

Ask Claude to consider different viewpoints:

```python
user_message = f"""...

Analyze from these perspectives:

**Security Engineer's View:**
- Is this update addressing CVEs?
- Does it introduce new dependencies?
- Any known vulnerabilities?

**DevOps Engineer's View:**
- Will this affect deployments?
- Any infrastructure changes?
- Rollback complexity?

**Developer's View:**
- API changes?
- Learning curve?
- Documentation quality?

**Product Manager's View:**
- User-facing impact?
- Feature enablement?
- Timeline considerations?

After considering all perspectives, make your decision.
"""
```

## Prompt Tuning Tips

### 1. Be Specific

**Bad**: "Decide if this should merge"
**Good**: "Analyze the security, performance, and compatibility implications. Make a merge decision with detailed reasoning."

### 2. Set Constraints

```python
"""
**Hard Constraints:**
- NEVER merge if CI fails
- NEVER merge major updates to: react, next, django
- ALWAYS use check_cve_database for security updates

**Soft Preferences:**
- Prefer auto-merge for type definitions
- Prefer approval for first-time dependencies
- Prefer blocking if bundle size increases >20%
"""
```

### 3. Provide Context

```python
f"""
**About This Project:**
- Type: Production e-commerce site
- Users: 1M+ daily
- Tech: React + Node.js + PostgreSQL
- Test coverage: 87%
- Deploy frequency: 3x per week

**Risk Tolerance:**
- LOW for: frontend (user-facing)
- MEDIUM for: backend APIs
- HIGH for: internal tools

Analyze the PR with this context...
"""
```

### 4. Use Positive Instructions

**Bad**: "Don't merge without checking release notes"
**Good**: "Always review release notes using the fetch_release_notes tool before making a decision"

### 5. Calibrate Confidence

```python
"""
**Confidence Guidelines:**
- If confidence < 70%: REQUIRE_APPROVAL
- If confidence < 50%: Explain what information would increase confidence
- If any doubt about security: REQUIRE_APPROVAL

Include confidence score in your response.
"""
```

## Testing Prompt Changes

### A/B Testing

```python
# Version A: Conservative
conservative_prompt = """You are very conservative..."""

# Version B: Balanced
balanced_prompt = """You balance speed and safety..."""

# Run both on same dataset
results_a = test_prompt(conservative_prompt, test_prs)
results_b = test_prompt(balanced_prompt, test_prs)

# Compare:
# - Auto-merge rate
# - False positive rate
# - Reasoning quality
```

### Regression Testing

```python
# Test cases with known good decisions
test_cases = [
    {
        "pr": patch_update_with_passing_ci,
        "expected": "AUTO_MERGE",
        "reason_should_include": ["patch", "CI passing"]
    },
    {
        "pr": major_update_react,
        "expected": "REQUIRE_APPROVAL",
        "reason_should_include": ["major", "React", "breaking"]
    }
]

# Test prompt changes don't break known good decisions
for case in test_cases:
    decision, reasoning = agent.decide(case["pr"])
    assert decision == case["expected"]
    assert all(keyword in reasoning for keyword in case["reason_should_include"])
```

## Common Customizations

### By Industry

#### Financial Services

```python
"""
**Regulatory Compliance**:
- ALL dependency changes must be audited
- NO auto-merge (regulatory requirement)
- Document ALL decisions with reasoning
- Check for license compliance

Always return REQUIRE_APPROVAL with detailed audit trail.
"""
```

#### Startup / Fast-Moving

```python
"""
**Move Fast**:
- Trust CI completely
- Auto-merge minor/patch if tests pass
- Only block on CI failure
- Speed is paramount

Be aggressive. We can rollback if needed.
"""
```

### By Team Maturity

#### Junior Team

```python
"""
**Educational Approach**:
- Explain reasoning in simple terms
- Highlight learning opportunities
- Point out potential issues
- Suggest what to check in code review

Default to REQUIRE_APPROVAL with educational reasoning.
"""
```

#### Senior Team

```python
"""
**Trust Team Judgment**:
- Be concise in reasoning
- Focus on non-obvious risks
- Assume team understands fundamentals
- Only flag truly concerning issues

Auto-merge unless specific risks identified.
"""
```

## Monitoring Prompt Effectiveness

### Metrics to Track

1. **Decision Distribution**
   ```
   Auto-merge: 60%
   Require approval: 30%
   Block: 10%
   ```

2. **Override Rate**
   ```
   Human overrides bot decision: <5%
   ```

3. **Incident Rate**
   ```
   Auto-merged PRs causing incidents: <1%
   ```

4. **Time Saved**
   ```
   Average review time: -70%
   Merges per week: +150%
   ```

### Feedback Loop

```python
# Track outcomes
{
    "pr_number": 123,
    "decision": "AUTO_MERGE",
    "outcome": "success",  # or "reverted", "incident"
    "time_to_merge": "2 minutes"
}

# Analyze patterns
failed_auto_merges = [
    outcome for outcome in outcomes
    if outcome["decision"] == "AUTO_MERGE" and outcome["outcome"] == "reverted"
]

# Adjust prompt based on failures
```

## Examples: Before & After

### Before: Generic

```python
"""You are a dependency agent. Analyze PRs and make merge decisions."""
```

**Result**: Inconsistent decisions, unclear reasoning

### After: Specific

```python
"""You are an expert dependency management agent for a production SaaS application.

**Core Responsibility**: Balance velocity with stability. Default to safety.

**Critical Dependencies** (always require review):
- Frontend: react, next, vue
- Backend: fastapi, sqlalchemy
- Infrastructure: terraform, docker

**Decision Framework**:
[Detailed framework...]

**Available Tools**:
[Tool descriptions...]

**Output Format**:
[JSON schema...]

Always explain your reasoning citing specific factors.
"""
```

**Result**: Consistent, well-reasoned decisions

## Resources

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
- [Claude's Constitutional AI](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback)
- [Few-Shot Learning](https://www.anthropic.com/research/few-shot-learning)

## Next Steps

1. Start with the default prompt
2. Monitor decisions for a week
3. Identify patterns (too conservative? too aggressive?)
4. Adjust prompt based on your team's needs
5. A/B test changes
6. Iterate based on outcomes

---

**Remember**: The prompt is your primary interface to Claude's reasoning. Invest time in making it clear, specific, and aligned with your team's values.
