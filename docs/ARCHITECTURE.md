# Architecture Guide

## Overview

LLM Dependency Bot implements a true **agentic AI architecture** where an LLM (Claude 3.5 Sonnet) serves as the reasoning engine for autonomous decision-making.

## Core Principles

### 1. Agentic AI Loop

```
┌──────────────────────────────────────────────────────────┐
│                     AGENTIC AI LOOP                       │
└──────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │  PERCEIVE   │  ← Gather context about PR
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   DECIDE    │  ← Claude analyzes and reasons
    └──────┬──────┘    • Can use tools autonomously
           │            • Iterates until confident
           ▼            • Provides natural language reasoning
    ┌─────────────┐
    │     ACT     │  ← Execute the decision
    └─────────────┘
```

### 2. LLM as Reasoning Engine

Unlike rule-based systems, the LLM makes contextual decisions:

**Rule-Based (Old)**:
```python
if update_type == "major":
    return REQUIRE_APPROVAL
elif update_type == "patch" and ci_passed:
    return AUTO_MERGE
```

**LLM-Based (This)**:
```python
decision = claude.analyze(
    context=pr_context,
    tools=[fetch_notes, check_cve, analyze_diff],
    reasoning=True
)
# Claude considers nuances, can gather more info, explains reasoning
```

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Actions                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   action.yml                          │  │
│  │  • Triggers on PR events                             │  │
│  │  • Sets up environment                               │  │
│  │  • Invokes agent.py                                  │  │
│  └──────────────────┬───────────────────────────────────┘  │
└────────────────────┼──────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLMDependencyBot                          │
│                     (agent.py)                               │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  PERCEPTION LAYER                                   │    │
│  │  • gather_pr_context()                             │    │
│  │  • _get_ci_status()                                │    │
│  │  • _parse_dependency_info()                        │    │
│  │  • _is_security_update()                           │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                      │                                       │
│                      ▼                                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  DECISION LAYER                                     │    │
│  │  • decide_with_llm()                               │    │
│  │    ├─ Calls Claude API                             │    │
│  │    ├─ Provides tools for Claude                    │    │
│  │    ├─ Handles agentic loop                         │    │
│  │    └─ Parses decision + reasoning                  │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                      │                                       │
│                      ▼                                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ACTION LAYER                                       │    │
│  │  • execute_action()                                │    │
│  │    ├─ _auto_merge()                                │    │
│  │    ├─ _request_review()                            │    │
│  │    └─ _add_blocking_comment()                      │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
          ┌──────────────────────┐
          │   External Services   │
          ├──────────────────────┤
          │ • GitHub API          │
          │ • Anthropic API       │
          │ • (Future: CVE DBs)   │
          └──────────────────────┘
```

## Detailed Component Breakdown

### 1. Perception Layer

**Purpose**: Gather all relevant information about a dependency PR.

**Key Functions**:

```python
def gather_pr_context(pr_number: int) -> PRContext:
    """
    Collects:
    - PR metadata (title, author, labels)
    - CI/CD status
    - Dependency information (name, versions, type)
    - Security indicators
    - Files changed
    """
```

**Data Structure**:

```python
@dataclass
class PRContext:
    number: int
    title: str
    body: str
    labels: List[str]
    author: str
    is_draft: bool
    mergeable: bool
    mergeable_state: str
    ci_status: str              # success, failure, pending
    ci_conclusion: Optional[str]
    update_type: str            # major, minor, patch
    old_version: str
    new_version: str
    dependency_name: str
    is_security_update: bool
    target_branch: str
    files_changed: List[str]
```

**Parsing Logic**:

1. **Version Detection**:
   ```python
   # Supports: "Bump axios from 1.6.0 to 1.6.1"
   # Supports: "Update react to 18.3.0"
   version_match = re.search(r'from ([\d.]+) to ([\d.]+)', title)
   ```

2. **Semantic Versioning**:
   ```python
   # Determines: major, minor, patch
   if old_parts[0] != new_parts[0]:
       update_type = "major"
   elif old_parts[1] != new_parts[1]:
       update_type = "minor"
   else:
       update_type = "patch"
   ```

3. **Security Detection**:
   ```python
   # Checks:
   # - Labels containing "security"
   # - Body mentions "CVE" or "vulnerability"
   ```

### 2. Decision Layer (THE MAGIC ✨)

**Purpose**: Use Claude to make intelligent, contextual decisions.

**Agentic Loop**:

```python
def decide_with_llm(context: PRContext) -> Tuple[MergeDecision, RiskLevel, str]:
    messages = [{"role": "user", "content": analysis_prompt}]

    for iteration in range(max_iterations=5):
        response = claude.create(
            system=AGENT_SYSTEM_PROMPT,
            tools=get_tools_definition(),
            messages=messages
        )

        if response.stop_reason == "tool_use":
            # Claude wants to use a tool
            for tool_call in response.content:
                result = execute_tool(tool_call.name, tool_call.input)
                messages.append(tool_result)
            continue  # Claude will process tool results
        else:
            # Claude has made final decision
            break

    return parse_decision(response)
```

**Tool Use Pattern**:

Claude can autonomously call these tools:

1. **fetch_release_notes**
   ```python
   # Claude decides: "Let me check the release notes for breaking changes"
   result = fetch_release_notes("react", "19.0.0")
   # Claude reads and incorporates into decision
   ```

2. **check_cve_database**
   ```python
   # Claude decides: "This is a security update, let me verify CVE details"
   result = check_cve_database("axios", "1.6.1")
   ```

3. **analyze_diff**
   ```python
   # Claude decides: "Only lock files changed? Let me verify"
   result = analyze_diff(pr_number=123)
   ```

**System Prompt**:

The system prompt defines Claude's role and decision framework:

```python
AGENT_SYSTEM_PROMPT = """You are an expert dependency management agent.

Your role: Analyze PRs and make merge decisions based on risk.

Available tools:
- fetch_release_notes
- check_cve_database
- analyze_diff

Decision framework:
1. AUTO_MERGE: Patch updates, passing CI, no breaking changes
2. REQUIRE_APPROVAL: Major updates, critical deps, warnings
3. DO_NOT_MERGE: CI failure, conflicts, vulnerabilities

Always explain your reasoning with specific factors."""
```

**Decision Parsing**:

Claude returns JSON:

```json
{
  "decision": "AUTO_MERGE",
  "risk_level": "LOW",
  "reasoning": "This is a patch update for axios with passing CI...",
  "key_factors": [
    "Patch version (1.6.0 → 1.6.1)",
    "CI passing (all 127 tests)",
    "Only lock files changed",
    "No breaking changes in release notes"
  ]
}
```

### 3. Action Layer

**Purpose**: Execute Claude's decision.

**Actions**:

1. **Auto-Merge**:
   ```python
   def _auto_merge(context, risk, reasoning):
       # Add explanatory comment
       comment = format_decision(decision, reasoning)
       add_comment(pr_number, comment)

       # Merge PR
       github.merge_pull_request(
           number=pr_number,
           method="squash",
           commit_message=f"Auto-merged: {reasoning[:200]}"
       )
   ```

2. **Request Review**:
   ```python
   def _request_review(context, risk, reasoning):
       # Add comment explaining why review needed
       add_comment(pr_number, comment)

       # Add labels for visibility
       add_labels(pr_number, ["needs-review", "llm-flagged"])
   ```

3. **Block**:
   ```python
   def _add_blocking_comment(context, risk, reasoning):
       # Explain why PR cannot be merged
       comment = format_blocking_reason(reasoning)
       add_comment(pr_number, comment)
   ```

## Data Flow

### Complete Flow Example

```
1. Dependabot opens PR: "Bump axios from 1.6.0 to 1.6.1"
                │
                ▼
2. GitHub Actions triggers on PR event
                │
                ▼
3. PERCEIVE: gather_pr_context(123)
   ├─ Fetch PR data from GitHub API
   ├─ Parse: dependency="axios", old="1.6.0", new="1.6.1", type="patch"
   ├─ Get CI status: "success"
   └─ Return PRContext object
                │
                ▼
4. DECIDE: decide_with_llm(context)
   ├─ Build analysis prompt with context
   ├─ Call Claude API with tools
   │
   ├─ [Iteration 1]
   │  Claude: "I see this is a patch update. CI is passing.
   │           Let me check the release notes to be sure."
   │  Tool call: fetch_release_notes("axios", "1.6.1")
   │
   ├─ [Iteration 2]
   │  Tool result: "Bug fixes only, no breaking changes"
   │  Claude: "Based on the release notes showing only bug fixes,
   │           CI passing, and patch version, this is safe."
   │  Decision: AUTO_MERGE, Risk: LOW
   │
   └─ Return (AUTO_MERGE, LOW, reasoning)
                │
                ▼
5. ACT: execute_action(context, AUTO_MERGE, LOW, reasoning)
   ├─ Add comment with Claude's reasoning
   ├─ Merge PR with commit message
   └─ Log success
                │
                ▼
6. PR merged ✅
```

## Key Design Patterns

### 1. Dataclass for Context

Using `@dataclass` for type safety and clarity:

```python
@dataclass
class PRContext:
    number: int
    title: str
    # ... all fields with types
```

**Benefits**:
- Type checking
- Auto-generated `__init__`
- Serialization support
- Clear contract

### 2. Enum for Decisions

```python
class MergeDecision(Enum):
    AUTO_MERGE = "auto_merge"
    REQUIRE_APPROVAL = "require_approval"
    DO_NOT_MERGE = "do_not_merge"
```

**Benefits**:
- Type safety
- Autocomplete
- Prevents typos

### 3. Tool Use Pattern

```python
# 1. Define tools
tools = [
    {
        "name": "tool_name",
        "description": "What it does",
        "input_schema": {...}
    }
]

# 2. LLM decides to use tool
if response.stop_reason == "tool_use":
    result = execute_tool(tool_name, tool_input)

# 3. Feed result back to LLM
messages.append(tool_result)
```

This is the **standard pattern** for agentic AI.

### 4. Fallback Logic

Always have a backup:

```python
try:
    decision = parse_llm_decision(response)
except ParseError:
    decision = fallback_rule_based_decision(context)
```

**Why**:
- LLM might return unexpected format
- API might be down
- Ensures system always works

## Scalability Considerations

### Current Limitations

1. **Synchronous Processing**
   - Processes one PR at a time
   - Each LLM call takes 2-5 seconds

2. **No Caching**
   - Same dependency analyzed multiple times
   - No learning from past decisions

3. **Limited Tools**
   - Tool implementations are stubs
   - No real CVE integration

### Future Enhancements

1. **Parallel Processing**
   ```python
   async def process_multiple_prs(pr_numbers):
       tasks = [decide_with_llm(pr) for pr in pr_numbers]
       results = await asyncio.gather(*tasks)
   ```

2. **Decision Caching**
   ```python
   cache_key = f"{dependency}:{old_ver}:{new_ver}"
   if cache_key in decision_cache:
       return cached_decision
   ```

3. **Multi-Agent Architecture**
   ```python
   security_agent = SecurityAgent()
   compat_agent = CompatibilityAgent()
   perf_agent = PerformanceAgent()

   coordinator = CoordinatorAgent([
       security_agent,
       compat_agent,
       perf_agent
   ])

   decision = coordinator.aggregate_decisions()
   ```

## Testing Architecture

### Test Strategy

1. **Unit Tests**: Test individual functions
   ```python
   def test_parse_dependency_info():
       title = "Bump axios from 1.0.0 to 1.1.0"
       type, old, new, name = parse(title)
       assert type == "minor"
   ```

2. **Mock External Calls**:
   ```python
   @patch('agent.LLMDependencyBot._make_request')
   def test_gather_context(mock_request):
       mock_request.return_value.json.return_value = {...}
       context = bot.gather_pr_context(123)
   ```

3. **Integration Tests**: Test full workflow
   ```python
   def test_full_workflow():
       # Mock GitHub and Anthropic
       with mock_github(), mock_claude():
           bot.run(pr_number=123)
           assert_pr_merged()
   ```

## Security Architecture

### Principle: Defense in Depth

1. **Input Validation**
   - Verify PR is from trusted bot
   - Sanitize inputs
   - Validate CI status

2. **Minimal Permissions**
   - Only required GitHub permissions
   - Scoped API tokens
   - No write access to secrets

3. **Audit Trail**
   - All decisions logged
   - Reasoning included in commits
   - PR comments for transparency

4. **Fallback Safety**
   - Default to human review on errors
   - Never merge if uncertain
   - Conservative system prompt

## Performance Characteristics

### Latency

```
Total time per PR: ~5-15 seconds

Breakdown:
- Gather context: 1-2s (GitHub API calls)
- Claude decision: 2-5s (LLM inference)
- Tool use (if any): +2-3s per tool
- Execute action: 1-2s (GitHub API)
```

### Cost

```
Per PR analysis: $0.01 - $0.05

Breakdown:
- Input tokens: ~1,000 tokens ($0.003)
- Output tokens: ~500 tokens ($0.015)
- Tool use: +500 tokens per tool ($0.015)

For 50 PRs/month: ~$2.50/month
```

### Rate Limits

```
GitHub API: 5,000 requests/hour
Anthropic API: Tier-dependent (500+ RPM typical)

Bot uses: ~5-10 GitHub requests per PR
Bot uses: 1-3 Anthropic requests per PR (with tools)
```

## Extensibility Points

### 1. Add New Tools

```python
def _your_custom_tool(self, param: str) -> str:
    """Your tool implementation"""
    return result

# Register in _get_tools_definition()
```

### 2. Custom Decision Logic

Modify `AGENT_SYSTEM_PROMPT` or add preprocessing:

```python
def decide_with_llm(self, context):
    # Add custom logic before LLM
    if context.dependency_name == "special-lib":
        return REQUIRE_APPROVAL

    # Continue with LLM
    return super().decide_with_llm(context)
```

### 3. Additional Context

Extend `PRContext`:

```python
@dataclass
class PRContext:
    # ... existing fields
    performance_impact: Optional[str] = None
    bundle_size_change: Optional[int] = None
```

## Conclusion

This architecture demonstrates modern agentic AI:
- **LLM as reasoning engine** (not just text generation)
- **Autonomous tool use** (LLM decides when to gather info)
- **Explainable decisions** (natural language reasoning)
- **Production-ready** (error handling, fallbacks, testing)

The pattern used here applies to many domains beyond dependency management:
- Code review automation
- Security analysis
- Performance optimization
- DevOps automation

**Key insight**: The LLM doesn't need to be perfect. It needs to be:
1. Good enough most of the time
2. Transparent about its reasoning
3. Have human oversight for edge cases
