#!/usr/bin/env python3
"""
LLM-Powered Dependency Bot

An autonomous AI agent that uses Claude to make intelligent decisions about
dependency update pull requests.

Architecture:
    PERCEIVE (gather context) → DECIDE (Claude analyzes) → ACT (execute)

This implements true agentic AI where an LLM serves as the reasoning engine,
autonomously using tools to gather information and making contextual decisions.

Author: LLM Dependency Bot Contributors
License: MIT
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import requests
from anthropic import Anthropic


class RiskLevel(Enum):
    """Risk assessment levels for dependency updates."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MergeDecision(Enum):
    """Possible merge decisions the agent can make."""

    AUTO_MERGE = "auto_merge"
    REQUIRE_APPROVAL = "require_approval"
    DO_NOT_MERGE = "do_not_merge"


@dataclass
class PRContext:
    """
    Complete context about a pull request (Perception Layer).

    This dataclass captures all information the agent needs to make
    an informed decision about a dependency update.
    """

    number: int
    title: str
    body: str
    labels: list[str]
    author: str
    is_draft: bool
    mergeable: bool
    mergeable_state: str
    ci_status: str
    ci_conclusion: Optional[str]
    update_type: str
    old_version: str
    new_version: str
    dependency_name: str
    is_security_update: bool
    target_branch: str
    files_changed: list[str]


class LLMDependencyBot:
    """
    An LLM-powered autonomous agent for dependency management.

    This agent demonstrates modern agentic AI architecture:
    - Uses Claude 3.5 Sonnet as the reasoning engine
    - Employs tool use (function calling) to gather additional context
    - Makes explainable decisions with natural language reasoning
    - Executes actions based on risk assessment

    Example:
        >>> bot = LLMDependencyBot(github_token, repo, anthropic_key)
        >>> bot.run(pr_number=123)
    """

    # System prompt defining the agent's role, capabilities, and decision framework
    AGENT_SYSTEM_PROMPT = """You are an expert dependency management agent for software projects.

Your role is to analyze dependency update pull requests and make intelligent merge decisions
based on risk assessment, testing results, and contextual information.

**Available Tools:**
- fetch_release_notes: Get release notes to check for breaking changes
- check_cve_database: Check for known security vulnerabilities
- analyze_diff: Review actual code changes in the PR

**Decision Framework:**

1. **AUTO_MERGE** - Safe to merge immediately:
   - Patch updates (1.0.0 → 1.0.1) with passing CI
   - Minor updates (1.0.0 → 1.1.0) with passing CI and no breaking changes
   - Security updates with passing CI (prioritize regardless of version)
   - Type definition updates (@types/*, *-types)

2. **REQUIRE_APPROVAL** - Needs human review:
   - Major version updates (1.0.0 → 2.0.0)
   - Breaking changes mentioned in release notes
   - Critical dependencies (frameworks, core libraries)
   - CI passed with warnings
   - Pre-release versions

3. **DO_NOT_MERGE** - Block the PR:
   - CI checks failed
   - Merge conflicts present
   - PR is in draft state
   - Known security vulnerabilities in new version
   - Cannot determine safety

**Important:** Always explain your reasoning clearly, citing specific factors from the
context and any tool results. Be conservative - when in doubt, require human approval."""

    def __init__(
        self, github_token: str, repo: str, anthropic_key: str, skip_author_check: bool = False
    ):
        """
        Initialize the LLM Dependency Bot.

        Args:
            github_token: GitHub API token with repo permissions
            repo: Repository in format "owner/name"
            anthropic_key: Anthropic API key for Claude
            skip_author_check: Skip author validation for testing purposes
        """
        self.github_token = github_token
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.skip_author_check = skip_author_check

        # Initialize Claude client
        self.anthropic = Anthropic(api_key=anthropic_key)

        # Configuration for critical dependencies that need extra scrutiny
        self.critical_dependencies = [
            "next",
            "react",
            "vue",
            "angular",
            "svelte",
            "fastapi",
            "django",
            "flask",
            "express",
            "langchain",
            "openai",
            "anthropic",
            "numpy",
            "pandas",
            "tensorflow",
            "pytorch",
        ]

    def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        """
        Make a GitHub API request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests.request()

        Returns:
            Response object

        Raises:
            requests.exceptions.HTTPError: If request fails
        """
        url = f"{self.api_base}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response

    def gather_pr_context(self, pr_number: int) -> PRContext:
        """
        PERCEPTION LAYER: Gather comprehensive context about a PR.

        This method collects all relevant information needed to make an
        informed decision about the dependency update.

        Args:
            pr_number: Pull request number

        Returns:
            PRContext with all gathered information
        """
        print(f"📊 Gathering context for PR #{pr_number}...")

        # Fetch PR details from GitHub API
        pr_data = self._make_request("GET", f"/repos/{self.repo}/pulls/{pr_number}").json()

        # Get CI/CD check status
        ci_status, ci_conclusion = self._get_ci_status(pr_number, pr_data["head"]["sha"])

        # Parse dependency information from PR title/body
        update_type, old_ver, new_ver, dep_name = self._parse_dependency_info(
            pr_data["title"], pr_data.get("body", "")
        )

        # Check if this is a security update
        is_security = self._is_security_update(pr_data["labels"], pr_data.get("body", ""))

        # Get list of changed files
        files = self._get_files_changed(pr_number)

        context = PRContext(
            number=pr_number,
            title=pr_data["title"],
            body=pr_data.get("body", ""),
            labels=[label["name"] for label in pr_data["labels"]],
            author=pr_data["user"]["login"],
            is_draft=pr_data["draft"],
            mergeable=pr_data.get("mergeable", False),
            mergeable_state=pr_data.get("mergeable_state", "unknown"),
            ci_status=ci_status,
            ci_conclusion=ci_conclusion,
            update_type=update_type,
            old_version=old_ver,
            new_version=new_ver,
            dependency_name=dep_name,
            is_security_update=is_security,
            target_branch=pr_data["base"]["ref"],
            files_changed=files,
        )

        # Log gathered context
        print(f"   ✓ Author: {context.author}")
        print(f"   ✓ Labels: {', '.join(context.labels) if context.labels else 'none'}")
        print(f"   ✓ CI Status: {context.ci_status}")
        print(
            f"   ✓ Update: {context.dependency_name} {context.old_version} → {context.new_version}"
        )
        print(f"   ✓ Type: {context.update_type}")

        return context

    def _get_ci_status(self, pr_number: int, sha: str) -> tuple[str, Optional[str]]:
        """
        Get the combined CI/CD status for a PR.

        Args:
            pr_number: Pull request number
            sha: Git commit SHA

        Returns:
            Tuple of (status, conclusion)
        """
        try:
            response = self._make_request("GET", f"/repos/{self.repo}/commits/{sha}/check-runs")
            check_runs = response.json().get("check_runs", [])

            if not check_runs:
                return "pending", None

            statuses = [run["status"] for run in check_runs]
            conclusions = [run["conclusion"] for run in check_runs if run.get("conclusion")]

            # Check if all runs completed
            if any(s != "completed" for s in statuses):
                return "pending", None

            # Check conclusions
            if all(c == "success" for c in conclusions):
                return "success", "success"
            elif any(c in ["failure", "cancelled", "timed_out"] for c in conclusions):
                return "failure", "failure"
            else:
                return "pending", None
        except Exception as e:
            print(f"   ⚠️  Could not fetch CI status: {e}")
            return "unknown", None

    def _parse_dependency_info(self, title: str, body: str) -> tuple[str, str, str, str]:
        """
        Parse dependency update information from PR title and body.

        Supports common formats from Dependabot, Renovate, etc.

        Args:
            title: PR title
            body: PR body/description

        Returns:
            Tuple of (update_type, old_version, new_version, dependency_name)
        """
        update_type = "unknown"
        dependency_name = "unknown"
        old_version = ""
        new_version = ""

        # Extract dependency name (Dependabot format)
        bump_match = re.search(r"Bump (.+?) from", title, re.IGNORECASE)
        if bump_match:
            dependency_name = bump_match.group(1).strip()

        # Renovate format
        if not bump_match:
            renovate_match = re.search(r"Update (.+?) to", title, re.IGNORECASE)
            if renovate_match:
                dependency_name = renovate_match.group(1).strip()

        # Extract version information
        version_match = re.search(r"from ([\d.]+(?:-[\w.]+)?) to ([\d.]+(?:-[\w.]+)?)", title)
        if version_match:
            old_version = version_match.group(1)
            new_version = version_match.group(2)

            # Determine semantic version update type
            old_parts = old_version.split(".")
            new_parts = new_version.split(".")

            if len(old_parts) >= 1 and len(new_parts) >= 1:
                if old_parts[0] != new_parts[0]:
                    update_type = "major"
                elif len(old_parts) >= 2 and len(new_parts) >= 2 and old_parts[1] != new_parts[1]:
                    update_type = "minor"
                else:
                    update_type = "patch"

        return update_type, old_version, new_version, dependency_name

    def _is_security_update(self, labels: list[dict[str, Any]], body: str) -> bool:
        """
        Check if this is a security-related update.

        Args:
            labels: List of PR labels
            body: PR description

        Returns:
            True if security update
        """
        label_names = [label["name"].lower() for label in labels]
        body_lower = body.lower()

        return (
            any("security" in label for label in label_names)
            or "security" in body_lower
            or "cve" in body_lower
            or "vulnerability" in body_lower
        )

    def _get_files_changed(self, pr_number: int) -> list[str]:
        """
        Get list of files changed in the PR.

        Args:
            pr_number: Pull request number

        Returns:
            List of file paths (limited to first 10)
        """
        try:
            files = self._make_request("GET", f"/repos/{self.repo}/pulls/{pr_number}/files").json()
            return [f["filename"] for f in files[:10]]
        except Exception:
            return []

    # ========================================================================
    # TOOL DEFINITIONS - Functions Claude can call to gather more context
    # ========================================================================

    def _fetch_release_notes(self, dependency: str, version: str) -> str:
        """
        Tool: Fetch release notes for a dependency version.

        In production, this would integrate with:
        - npm registry for JavaScript packages
        - PyPI for Python packages
        - GitHub Releases API for GitHub-hosted packages

        Args:
            dependency: Name of the dependency
            version: Version number

        Returns:
            Release notes or error message
        """
        print(f"   🔍 Claude requesting release notes for {dependency} {version}...")

        # TODO: Implement actual release notes fetching
        # For now, return a placeholder
        return f"Release notes for {dependency} {version} would be fetched from package registry (npm, PyPI, etc.) in production implementation."

    def _check_cve_database(self, dependency: str, version: str) -> str:
        """
        Tool: Check if a version has known CVE vulnerabilities.

        In production, this would integrate with:
        - GitHub Security Advisories
        - npm audit / pip-audit
        - Snyk, Dependabot alerts, etc.

        Args:
            dependency: Name of the dependency
            version: Version number

        Returns:
            CVE information or error message
        """
        print(f"   🔍 Claude checking CVE database for {dependency} {version}...")

        # TODO: Implement actual CVE checking
        return f"CVE check for {dependency} {version} would query vulnerability databases (GitHub Security, Snyk, etc.) in production implementation."

    def _analyze_diff(self, pr_number: int) -> str:
        """
        Tool: Get the actual code changes in the PR.

        Args:
            pr_number: Pull request number

        Returns:
            Diff content or error message
        """
        print(f"   🔍 Claude analyzing diff for PR #{pr_number}...")

        try:
            response = self._make_request(
                "GET",
                f"/repos/{self.repo}/pulls/{pr_number}",
                headers={**self.headers, "Accept": "application/vnd.github.v3.diff"},
            )
            diff = response.text

            # Truncate if too long to fit in context
            if len(diff) > 2000:
                diff = diff[:2000] + "\n... (truncated for brevity)"

            return diff
        except Exception as e:
            return f"Could not fetch diff: {e}"

    def _get_tools_definition(self) -> list[dict[str, Any]]:
        """
        Define tools that Claude can use during analysis.

        Returns:
            List of tool definitions in Anthropic format
        """
        return [
            {
                "name": "fetch_release_notes",
                "description": "Fetch release notes for a specific version of a dependency to check for breaking changes, new features, or important updates",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "dependency": {"type": "string", "description": "Name of the dependency"},
                        "version": {"type": "string", "description": "Version number"},
                    },
                    "required": ["dependency", "version"],
                },
            },
            {
                "name": "check_cve_database",
                "description": "Check if a dependency version has known security vulnerabilities (CVEs)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "dependency": {"type": "string", "description": "Name of the dependency"},
                        "version": {"type": "string", "description": "Version number"},
                    },
                    "required": ["dependency", "version"],
                },
            },
            {
                "name": "analyze_diff",
                "description": "Get the actual code changes in the PR to understand what files are being modified",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pr_number": {"type": "integer", "description": "Pull request number"}
                    },
                    "required": ["pr_number"],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """
        Execute a tool call from Claude.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        if tool_name == "fetch_release_notes":
            return self._fetch_release_notes(tool_input["dependency"], tool_input["version"])
        elif tool_name == "check_cve_database":
            return self._check_cve_database(tool_input["dependency"], tool_input["version"])
        elif tool_name == "analyze_diff":
            return self._analyze_diff(tool_input["pr_number"])
        else:
            return f"Unknown tool: {tool_name}"

    def decide_with_llm(self, context: PRContext) -> tuple[MergeDecision, RiskLevel, str]:
        """
        DECISION LAYER: Use Claude to make intelligent merge decision.

        This is where the agentic AI magic happens:
        1. Claude analyzes the PR context
        2. Claude can autonomously use tools to gather more information
        3. Claude reasons through the decision
        4. Claude returns a decision with explanation

        Args:
            context: Complete PR context

        Returns:
            Tuple of (decision, risk_level, reasoning)
        """
        print(f"\n🤖 Asking Claude to analyze PR #{context.number}...")

        # Check if this is a critical dependency
        is_critical = any(
            crit in context.dependency_name.lower() for crit in self.critical_dependencies
        )

        # Build the analysis prompt
        user_message = f"""Analyze this dependency update PR and decide if it should be merged:

**PR Information:**
- Title: {context.title}
- Dependency: {context.dependency_name}
- Update: {context.old_version} → {context.new_version}
- Update Type: {context.update_type}
- Security Update: {context.is_security_update}
- CI Status: {context.ci_status}
- CI Conclusion: {context.ci_conclusion}
- Mergeable: {context.mergeable} ({context.mergeable_state})
- Draft: {context.is_draft}
- Labels: {', '.join(context.labels) if context.labels else 'none'}
- Critical Dependency: {is_critical}
- Files Changed: {', '.join(context.files_changed[:5]) if context.files_changed else 'none'}

**PR Body:**
{context.body[:800] if context.body else '(empty)'}

Based on this information:
1. Assess the risk level (LOW, MEDIUM, HIGH, or CRITICAL)
2. Make a merge decision (AUTO_MERGE, REQUIRE_APPROVAL, or DO_NOT_MERGE)
3. Explain your reasoning in detail

Use the available tools to gather additional information if needed.

Respond in JSON format:
{{
    "decision": "AUTO_MERGE|REQUIRE_APPROVAL|DO_NOT_MERGE",
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "reasoning": "Detailed explanation of your decision",
    "key_factors": ["factor 1", "factor 2", ...]
}}"""

        # Agentic loop: Claude can use tools multiple times
        messages = [{"role": "user", "content": user_message}]
        max_iterations = 5

        for iteration in range(max_iterations):
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=self.AGENT_SYSTEM_PROMPT,
                tools=self._get_tools_definition(),
                messages=messages,
            )

            print(f"   💭 Claude iteration {iteration + 1}...")

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Build assistant message with all content blocks
                assistant_content = []
                tool_results = []

                for content_block in response.content:
                    assistant_content.append(content_block)

                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input

                        # Execute the tool
                        tool_result = self._execute_tool(tool_name, tool_input)

                        # Prepare tool result for next message
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": tool_result,
                            }
                        )

                # Add assistant message with tool use
                messages.append({"role": "assistant", "content": assistant_content})  # type: ignore
                # Add user message with tool results
                messages.append({"role": "user", "content": tool_results})  # type: ignore

                # Continue the loop
                continue
            else:
                # Claude has made a final decision
                break

        # Extract final text response
        final_text = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                final_text += content_block.text

        print("\n   ✓ Claude's analysis complete\n")

        # Parse Claude's decision
        try:
            # Extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", final_text)
            if json_match:
                decision_data = json.loads(json_match.group())

                decision = MergeDecision[decision_data["decision"]]
                risk = RiskLevel[decision_data["risk_level"]]
                reasoning = decision_data["reasoning"]

                print(f"   📋 Decision: {decision.value}")
                print(f"   ⚖️  Risk: {risk.value}")

                return decision, risk, reasoning
            else:
                print("   ⚠️  Could not parse JSON, using fallback logic")
                return self._fallback_decision(context, final_text)

        except Exception as e:
            print(f"   ⚠️  Error parsing Claude's response: {e}")
            return self._fallback_decision(context, final_text)

    def _fallback_decision(
        self, context: PRContext, llm_response: str
    ) -> tuple[MergeDecision, RiskLevel, str]:
        """
        Fallback decision logic if LLM response cannot be parsed.

        Args:
            context: PR context
            llm_response: Raw LLM response

        Returns:
            Tuple of (decision, risk_level, reasoning)
        """
        reasoning = f"Fallback decision used due to parsing error.\n\n{llm_response[:500]}"

        if context.ci_status == "failure" or not context.mergeable:
            return MergeDecision.DO_NOT_MERGE, RiskLevel.CRITICAL, reasoning
        elif context.update_type == "major":
            return MergeDecision.REQUIRE_APPROVAL, RiskLevel.HIGH, reasoning
        elif context.is_security_update or context.update_type in ["minor", "patch"]:
            return MergeDecision.AUTO_MERGE, RiskLevel.LOW, reasoning
        else:
            return MergeDecision.REQUIRE_APPROVAL, RiskLevel.MEDIUM, reasoning

    def execute_action(
        self, context: PRContext, decision: MergeDecision, risk: RiskLevel, reasoning: str
    ) -> None:
        """
        ACTION LAYER: Execute the decided action.

        Args:
            context: PR context
            decision: Merge decision
            risk: Risk level
            reasoning: Claude's reasoning
        """
        print(f"\n🚀 Executing action: {decision.value}...")

        if decision == MergeDecision.AUTO_MERGE:
            self._auto_merge(context, risk, reasoning)
        elif decision == MergeDecision.REQUIRE_APPROVAL:
            self._request_review(context, risk, reasoning)
        else:
            self._add_blocking_comment(context, risk, reasoning)

    def _auto_merge(self, context: PRContext, risk: RiskLevel, reasoning: str) -> None:
        """Auto-merge the PR with explanation."""
        print(f"   🔀 Auto-merging PR #{context.number}...")

        comment = f"""🤖 **LLM Dependency Bot**

**Decision**: ✅ Auto-merge approved
**Risk Level**: {risk.value.upper()}

**Claude's Analysis**:
{reasoning}

**Context**:
- Dependency: `{context.dependency_name}`
- Update: `{context.old_version}` → `{context.new_version}` ({context.update_type})
- CI Status: {context.ci_status}

Merging automatically...

---
*Powered by [Claude 3.5 Sonnet](https://www.anthropic.com/claude) - Autonomous AI for intelligent dependency management*
"""
        self._add_comment(context.number, comment)

        # Merge the PR
        merge_data = {
            "commit_title": f"🤖 {context.title}",
            "commit_message": f"Auto-merged by LLM Dependency Bot\n\nRisk: {risk.value}\n\n{reasoning[:500]}",
            "merge_method": "squash",
        }

        try:
            self._make_request(
                "PUT", f"/repos/{self.repo}/pulls/{context.number}/merge", json=merge_data
            )
            print(f"   ✅ Successfully merged PR #{context.number}")
        except requests.exceptions.HTTPError as e:
            print(f"   ❌ Failed to merge: {e}")
            raise

    def _request_review(self, context: PRContext, risk: RiskLevel, reasoning: str) -> None:
        """Request human review for the PR."""
        print(f"   👤 Requesting human review for PR #{context.number}...")

        comment = f"""🤖 **LLM Dependency Bot**

**Decision**: 👤 Human review required
**Risk Level**: {risk.value.upper()}

**Claude's Analysis**:
{reasoning}

**Context**:
- Dependency: `{context.dependency_name}`
- Update: `{context.old_version}` → `{context.new_version}` ({context.update_type})
- CI Status: {context.ci_status}

Please review this update carefully before merging.

---
*Powered by [Claude 3.5 Sonnet](https://www.anthropic.com/claude) - Autonomous AI for intelligent dependency management*
"""
        self._add_comment(context.number, comment)

        try:
            self._add_labels(context.number, ["needs-review", "llm-flagged"])
        except Exception:  # noqa: E722
            print("   ⚠️  Could not add labels (may not have permission)")

        print("   ✅ Added review request")

    def _add_blocking_comment(self, context: PRContext, risk: RiskLevel, reasoning: str) -> None:
        """Add a blocking comment explaining why PR cannot be merged."""
        print(f"   🚫 Blocking PR #{context.number}...")

        comment = f"""🤖 **LLM Dependency Bot**

**Decision**: ❌ Cannot merge
**Risk Level**: {risk.value.upper()}

**Claude's Analysis**:
{reasoning}

**Context**:
- Dependency: `{context.dependency_name}`
- Update: `{context.old_version}` → `{context.new_version}` ({context.update_type})
- CI Status: {context.ci_status}
- Mergeable: {context.mergeable}

Please resolve the issues identified above before merging.

---
*Powered by [Claude 3.5 Sonnet](https://www.anthropic.com/claude) - Autonomous AI for intelligent dependency management*
"""
        self._add_comment(context.number, comment)
        print("   ✅ Added blocking comment")

    def _add_comment(self, pr_number: int, body: str) -> None:
        """Add a comment to a PR."""
        self._make_request(
            "POST", f"/repos/{self.repo}/issues/{pr_number}/comments", json={"body": body}
        )

    def _add_labels(self, pr_number: int, labels: list[str]) -> None:
        """Add labels to a PR."""
        self._make_request(
            "POST", f"/repos/{self.repo}/issues/{pr_number}/labels", json={"labels": labels}
        )

    def is_dependency_pr(self, pr_number: int) -> bool:
        """
        Check if a PR is a dependency update PR.

        Args:
            pr_number: Pull request number

        Returns:
            True if this is a dependency PR
        """
        pr_data = self._make_request("GET", f"/repos/{self.repo}/pulls/{pr_number}").json()
        author = pr_data["user"]["login"]

        # Check if from known dependency bots
        known_bots = ["dependabot[bot]", "dependabot", "renovate[bot]", "renovate"]
        if not self.skip_author_check and author not in known_bots:
            return False

        # Additional validation: check labels or title
        labels = [label["name"].lower() for label in pr_data["labels"]]
        title_lower = pr_data["title"].lower()

        return (
            any("dep" in label for label in labels)
            or "bump" in title_lower
            or "update" in title_lower
        )

    def run(self, pr_number: int) -> None:
        """
        Main agent loop: Perceive → Decide → Act.

        This is the core agentic AI loop where Claude serves as the
        reasoning engine to make autonomous decisions.

        Args:
            pr_number: Pull request number to analyze
        """
        print(f"\n{'='*70}")
        print("🤖 LLM Dependency Bot - Autonomous AI Agent")
        print("   Powered by Claude 3.5 Sonnet")
        print(f"{'='*70}\n")

        # Validate this is a dependency PR
        if not self.is_dependency_pr(pr_number):
            print(f"❌ PR #{pr_number} is not a dependency PR. Exiting.")
            return

        print(f"✅ Confirmed PR #{pr_number} is a dependency PR\n")

        # PERCEIVE: Gather comprehensive context
        context = self.gather_pr_context(pr_number)

        # DECIDE: Let Claude make the decision using tools
        decision, risk, reasoning = self.decide_with_llm(context)

        # ACT: Execute Claude's decision
        self.execute_action(context, decision, risk, reasoning)

        print(f"\n{'='*70}")
        print("✅ LLM Dependency Bot completed successfully")
        print(f"{'='*70}\n")


def main() -> None:
    """Entry point for the LLM Dependency Bot."""
    # Get configuration from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    pr_number_str = os.environ.get("PR_NUMBER")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    skip_author_check = os.environ.get("SKIP_AUTHOR_CHECK", "false").lower() == "true"

    # Validate required environment variables
    if not all([github_token, repository, pr_number_str, anthropic_key]):
        print("❌ Error: Missing required environment variables")
        print("   Required: GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER, ANTHROPIC_API_KEY")
        sys.exit(1)

    # Type guard to satisfy mypy
    assert github_token is not None
    assert repository is not None
    assert pr_number_str is not None
    assert anthropic_key is not None

    # Parse PR number
    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print(f"❌ Error: Invalid PR number: {pr_number_str}")
        sys.exit(1)

    # Initialize and run the bot
    bot = LLMDependencyBot(github_token, repository, anthropic_key, skip_author_check)

    try:
        bot.run(pr_number)
    except Exception as e:
        print(f"\n❌ Bot failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
