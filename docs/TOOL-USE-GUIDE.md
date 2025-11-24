# Tool Use Guide

Learn how to extend LLM Dependency Bot with custom tools that Claude can use autonomously.

## What Are Tools?

Tools (also called "functions" or "function calling") allow Claude to gather additional information or perform actions during its reasoning process.

**Example workflow:**

```
Claude: "This is a major React update. Let me check the release notes..."
→ Calls: fetch_release_notes("react", "19.0.0")
→ Receives: "Breaking changes: ..."
Claude: "Based on the breaking changes listed, I recommend human review."
```

## Built-in Tools

The bot includes three default tools:

### 1. fetch_release_notes

```python
def _fetch_release_notes(self, dependency: str, version: str) -> str:
    """
    Fetch release notes for a dependency version.

    Args:
        dependency: Package name (e.g., "axios", "react")
        version: Version number (e.g., "1.6.1")

    Returns:
        Release notes text or error message
    """
```

### 2. check_cve_database

```python
def _check_cve_database(self, dependency: str, version: str) -> str:
    """
    Check for known CVE vulnerabilities.

    Args:
        dependency: Package name
        version: Version number

    Returns:
        CVE information or "no vulnerabilities found"
    """
```

### 3. analyze_diff

```python
def _analyze_diff(self, pr_number: int) -> str:
    """
    Get the actual code changes in the PR.

    Args:
        pr_number: Pull request number

    Returns:
        Diff content (truncated if too large)
    """
```

## Creating Custom Tools

### Step 1: Implement the Tool Function

Add your tool implementation to `src/agent.py`:

```python
def _check_bundle_size(self, dependency: str, version: str) -> str:
    """
    Tool: Check if update increases bundle size significantly.

    Args:
        dependency: Package name
        version: Version to check

    Returns:
        Bundle size comparison
    """
    print(f"   🔍 Claude checking bundle size for {dependency} {version}...")

    try:
        # Your implementation here
        # Example: Query bundlephobia API
        response = requests.get(
            f"https://bundlephobia.com/api/size?package={dependency}@{version}"
        )
        data = response.json()

        return f"Bundle size: {data['size']} bytes (gzipped: {data['gzip']} bytes)"

    except Exception as e:
        return f"Could not fetch bundle size: {e}"
```

### Step 2: Register the Tool

Add tool definition to `_get_tools_definition()`:

```python
def _get_tools_definition(self) -> List[Dict[str, Any]]:
    return [
        # ... existing tools ...

        {
            "name": "check_bundle_size",
            "description": "Check the bundle size impact of updating a JavaScript dependency. Useful for frontend performance considerations.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "dependency": {
                        "type": "string",
                        "description": "Name of the JavaScript package"
                    },
                    "version": {
                        "type": "string",
                        "description": "Version number to check"
                    }
                },
                "required": ["dependency", "version"]
            }
        }
    ]
```

### Step 3: Handle Tool Execution

Add case to `_execute_tool()`:

```python
def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
    if tool_name == "fetch_release_notes":
        return self._fetch_release_notes(tool_input["dependency"], tool_input["version"])
    elif tool_name == "check_cve_database":
        return self._check_cve_database(tool_input["dependency"], tool_input["version"])
    elif tool_name == "analyze_diff":
        return self._analyze_diff(tool_input["pr_number"])
    elif tool_name == "check_bundle_size":
        return self._check_bundle_size(tool_input["dependency"], tool_input["version"])
    else:
        return f"Unknown tool: {tool_name}"
```

### Step 4: Update System Prompt (Optional)

Tell Claude about the new tool in `AGENT_SYSTEM_PROMPT`:

```python
AGENT_SYSTEM_PROMPT = """...

**Available Tools:**
- fetch_release_notes: Get release notes
- check_cve_database: Check for vulnerabilities
- analyze_diff: Review code changes
- check_bundle_size: Check frontend bundle size impact (use for JS packages)

..."""
```

## Advanced Tool Examples

### Example 1: Performance Impact Analysis

```python
def _check_performance_benchmarks(
    self,
    dependency: str,
    old_version: str,
    new_version: str
) -> str:
    """
    Compare performance between versions.

    This tool could:
    - Query npm/PyPI for benchmark data
    - Run actual benchmarks in a sandbox
    - Check GitHub issues for performance regressions
    """
    print(f"   🔍 Checking performance: {dependency} {old_version} → {new_version}...")

    # Example: Search GitHub issues for "performance regression"
    search_query = f"{dependency} {new_version} performance regression"

    # Your implementation...
    return f"Performance analysis for {dependency} {new_version}"
```

Tool definition:

```python
{
    "name": "check_performance_benchmarks",
    "description": "Analyze performance impact of updating to a new version. Checks for known performance regressions or improvements.",
    "input_schema": {
        "type": "object",
        "properties": {
            "dependency": {"type": "string"},
            "old_version": {"type": "string"},
            "new_version": {"type": "string"}
        },
        "required": ["dependency", "old_version", "new_version"]
    }
}
```

### Example 2: Dependency Tree Impact

```python
def _analyze_dependency_tree(self, dependency: str, version: str) -> str:
    """
    Analyze how many other packages depend on this one.

    High impact if many internal packages depend on it.
    """
    print(f"   🔍 Analyzing dependency tree for {dependency}...")

    # Example: Parse package-lock.json or requirements.txt
    # Find all packages that depend on this one

    dependents = find_dependents(dependency)

    if len(dependents) > 10:
        return f"HIGH IMPACT: {len(dependents)} packages depend on {dependency}"
    elif len(dependents) > 3:
        return f"MEDIUM IMPACT: {len(dependents)} packages depend on {dependency}"
    else:
        return f"LOW IMPACT: {len(dependents)} packages depend on {dependency}"
```

### Example 3: Team Notification

```python
def _notify_team_for_input(
    self,
    dependency: str,
    question: str
) -> str:
    """
    Ask the team for input on a dependency decision.

    Sends a Slack message and waits for response (with timeout).
    """
    print(f"   📢 Asking team about {dependency}...")

    slack_client = WebClient(token=os.environ["SLACK_TOKEN"])

    response = slack_client.chat_postMessage(
        channel="#dependencies",
        text=f"🤖 Bot needs input: {question}",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Dependency:* {dependency}\n\n{question}"}
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "Approve"}, "value": "approve"},
                    {"type": "button", "text": {"type": "plain_text", "text": "Reject"}, "value": "reject"}
                ]
            }
        ]
    )

    # In production, implement async waiting for response
    return "Team input requested via Slack"
```

### Example 4: Historical Analysis

```python
def _check_past_failures(
    self,
    dependency: str
) -> str:
    """
    Check if this dependency has caused issues before.

    Queries:
    - Past PRs that were reverted
    - GitHub issues mentioning this dependency
    - Internal incident database
    """
    print(f"   🔍 Checking history for {dependency}...")

    # Query GitHub for past issues
    past_issues = github_search(f"repo:owner/repo {dependency} is:issue")

    problem_issues = [
        issue for issue in past_issues
        if "bug" in issue.labels or "regression" in issue.labels
    ]

    if problem_issues:
        return f"⚠️  {len(problem_issues)} past issues found with {dependency}:\n" + \
               "\n".join([f"- {issue.title}" for issue in problem_issues[:3]])
    else:
        return f"✅ No historical issues found with {dependency}"
```

## Tool Design Best Practices

### 1. Keep Tools Focused

**Good**: Single purpose tools
```python
def _check_cve(dependency, version): ...
def _fetch_release_notes(dependency, version): ...
```

**Bad**: Kitchen sink tool
```python
def _analyze_everything(dependency, version):
    # Does CVE check, release notes, performance, etc.
    ...
```

### 2. Handle Errors Gracefully

```python
def _your_tool(self, param: str) -> str:
    try:
        result = risky_operation(param)
        return result
    except APIError as e:
        return f"API error: {e}. Unable to complete check."
    except Exception as e:
        return f"Unexpected error: {e}. Proceeding without this information."
```

**Why**: Tools should never crash the bot. Return error messages that Claude can understand.

### 3. Provide Rich Context

**Bad**:
```python
return "No vulnerabilities"
```

**Good**:
```python
return """CVE Check Results:
- Scanned version: 1.6.1
- Vulnerabilities found: 0
- Last scanned: 2024-01-15
- Database: NVD, Snyk, GitHub Security
"""
```

### 4. Respect Rate Limits

```python
def _api_call_with_retry(self, url: str) -> dict:
    """Make API call with exponential backoff."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise

    return {}
```

### 5. Optimize for LLM Context

**Bad**: Return entire file
```python
return huge_file_content  # 10,000 lines
```

**Good**: Summarize or truncate
```python
if len(content) > 2000:
    return content[:2000] + "\n... (truncated, showing first 2000 chars)"
return content
```

## Testing Custom Tools

### Unit Test

```python
def test_custom_tool(bot):
    """Test tool implementation."""
    result = bot._check_bundle_size("react", "18.3.0")

    assert "Bundle size:" in result
    assert "bytes" in result
```

### Integration Test

```python
@patch('src.agent.requests.get')
def test_tool_with_mock_api(mock_get, bot):
    """Test tool with mocked external API."""
    mock_get.return_value.json.return_value = {
        "size": 5000,
        "gzip": 2000
    }

    result = bot._check_bundle_size("react", "18.3.0")

    assert "5000 bytes" in result
```

### Test Tool Use in Agent

```python
@patch('src.agent.Anthropic')
def test_claude_uses_custom_tool(mock_anthropic, bot):
    """Test that Claude can use the custom tool."""
    # Mock Claude to request tool
    mock_response = MagicMock()
    mock_response.stop_reason = "tool_use"
    mock_response.content = [
        MagicMock(
            type="tool_use",
            name="check_bundle_size",
            input={"dependency": "react", "version": "18.3.0"}
        )
    ]

    mock_anthropic.return_value.messages.create.return_value = mock_response

    # Run agent
    context = sample_pr_context()
    bot.decide_with_llm(context)

    # Verify tool was called
    # Add assertions...
```

## Real-World Tool Implementations

### Implementing fetch_release_notes

```python
def _fetch_release_notes(self, dependency: str, version: str) -> str:
    """Real implementation for npm packages."""
    print(f"   🔍 Fetching release notes for {dependency}@{version}...")

    try:
        # Try npm registry
        response = requests.get(
            f"https://registry.npmjs.org/{dependency}/{version}"
        )
        data = response.json()

        # Get repository info
        repo_url = data.get("repository", {}).get("url", "")

        if "github.com" in repo_url:
            # Extract owner/repo from URL
            parts = repo_url.split("github.com/")[1].split("/")
            owner, repo = parts[0], parts[1].replace(".git", "")

            # Fetch GitHub release notes
            gh_response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/releases/tags/v{version}",
                headers={"Authorization": f"Bearer {self.github_token}"}
            )

            if gh_response.status_code == 200:
                release = gh_response.json()
                return f"Release Notes for {dependency} {version}:\n\n{release['body']}"

        # Fallback: return package description
        return data.get("description", "No release notes available")

    except Exception as e:
        return f"Could not fetch release notes: {e}"
```

### Implementing check_cve_database

```python
def _check_cve_database(self, dependency: str, version: str) -> str:
    """Real implementation using GitHub Security API."""
    print(f"   🔍 Checking CVE database for {dependency}@{version}...")

    try:
        # Use GitHub GraphQL API for security advisories
        query = """
        query($package: String!) {
          securityVulnerabilities(first: 10, package: $package) {
            nodes {
              advisory {
                summary
                severity
                identifiers { type value }
              }
              vulnerableVersionRange
            }
          }
        }
        """

        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"package": dependency}},
            headers={"Authorization": f"Bearer {self.github_token}"}
        )

        data = response.json()
        vulnerabilities = data["data"]["securityVulnerabilities"]["nodes"]

        # Check if version is affected
        affected = []
        for vuln in vulnerabilities:
            if is_version_affected(version, vuln["vulnerableVersionRange"]):
                affected.append(vuln)

        if affected:
            result = f"⚠️  {len(affected)} vulnerabilities found:\n\n"
            for vuln in affected:
                result += f"- {vuln['advisory']['severity']}: {vuln['advisory']['summary']}\n"
            return result
        else:
            return f"✅ No known vulnerabilities in {dependency}@{version}"

    except Exception as e:
        return f"Could not check CVE database: {e}"
```

## Tool Orchestration

### Sequential Tools

Claude can chain tools:

```
Claude iteration 1: Uses fetch_release_notes()
Claude iteration 2: Sees "performance improvements" in notes
                    Uses check_performance_benchmarks()
Claude iteration 3: Confirms improvement
                    Makes decision: AUTO_MERGE
```

### Conditional Tools

Claude decides which tools to use based on context:

```python
if update_type == "major":
    # Claude likely to use: fetch_release_notes, check_cve
elif is_security_update:
    # Claude likely to use: check_cve, analyze_diff
elif dependency in ["react", "vue"]:
    # Claude likely to use: check_bundle_size
```

## Common Pitfalls

### 1. Tool Timeout

**Problem**: Tool takes too long
**Solution**: Add timeout and return partial results

```python
def _slow_tool(self, param: str) -> str:
    try:
        result = requests.get(url, timeout=5)  # 5 second timeout
        return result.text
    except requests.Timeout:
        return "Analysis incomplete: timeout after 5 seconds"
```

### 2. Tool Dependencies

**Problem**: Tool requires external service
**Solution**: Check availability, provide fallback

```python
def _tool_with_dependency(self, param: str) -> str:
    if not os.environ.get("EXTERNAL_API_KEY"):
        return "Tool unavailable: EXTERNAL_API_KEY not configured"

    # Use the tool...
```

### 3. Circular Tool Use

**Problem**: Claude uses same tool repeatedly
**Solution**: Limit iterations

```python
for iteration in range(max_iterations=5):  # Prevent infinite loop
    ...
```

## Resources

- [Anthropic Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Function Calling Best Practices](https://www.anthropic.com/research/building-effective-agents)
- [Example Tool Implementations](../examples/)

## Next Steps

1. Start with simple tools (API lookups)
2. Test thoroughly with unit tests
3. Monitor Claude's tool usage in practice
4. Iterate based on what information Claude actually needs
5. Share your tools with the community!

---

**Remember**: Tools should augment Claude's reasoning, not replace it. The LLM decides when and how to use tools based on the specific context.
