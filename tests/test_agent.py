"""
Unit tests for the LLM Dependency Bot agent.

This test suite demonstrates testing patterns for AI agents,
including mocking LLM responses and GitHub API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agent import (
    LLMDependencyBot,
    RiskLevel,
    MergeDecision,
    PRContext,
)


@pytest.fixture
def mock_github_token():
    """Mock GitHub token."""
    return "ghp_mock_token_123"


@pytest.fixture
def mock_anthropic_key():
    """Mock Anthropic API key."""
    return "sk-ant-mock-key-123"


@pytest.fixture
def bot(mock_github_token, mock_anthropic_key):
    """Create a bot instance for testing."""
    return LLMDependencyBot(
        github_token=mock_github_token,
        repo="test-owner/test-repo",
        anthropic_key=mock_anthropic_key
    )


@pytest.fixture
def sample_pr_context():
    """Sample PR context for testing."""
    return PRContext(
        number=123,
        title="Bump axios from 1.6.0 to 1.6.1",
        body="Bumps [axios](https://github.com/axios/axios) from 1.6.0 to 1.6.1.",
        labels=["dependencies", "javascript"],
        author="dependabot[bot]",
        is_draft=False,
        mergeable=True,
        mergeable_state="clean",
        ci_status="success",
        ci_conclusion="success",
        update_type="patch",
        old_version="1.6.0",
        new_version="1.6.1",
        dependency_name="axios",
        is_security_update=False,
        target_branch="main",
        files_changed=["package.json", "package-lock.json"]
    )


class TestDependencyInfoParsing:
    """Test parsing of dependency information from PR title/body."""

    def test_parse_dependabot_format(self, bot):
        """Test parsing Dependabot-style PR title."""
        title = "Bump axios from 1.6.0 to 1.6.1"
        body = ""

        update_type, old_ver, new_ver, dep_name = bot._parse_dependency_info(title, body)

        assert dep_name == "axios"
        assert old_ver == "1.6.0"
        assert new_ver == "1.6.1"
        assert update_type == "patch"

    def test_parse_minor_update(self, bot):
        """Test parsing minor version update."""
        title = "Bump react from 18.2.0 to 18.3.0"
        body = ""

        update_type, old_ver, new_ver, dep_name = bot._parse_dependency_info(title, body)

        assert update_type == "minor"
        assert old_ver == "18.2.0"
        assert new_ver == "18.3.0"

    def test_parse_major_update(self, bot):
        """Test parsing major version update."""
        title = "Bump next from 13.5.0 to 14.0.0"
        body = ""

        update_type, old_ver, new_ver, dep_name = bot._parse_dependency_info(title, body)

        assert update_type == "major"
        assert old_ver == "13.5.0"
        assert new_ver == "14.0.0"


class TestSecurityDetection:
    """Test detection of security updates."""

    def test_security_label_detection(self, bot):
        """Test detection via security label."""
        labels = [{"name": "security"}]
        body = ""

        is_security = bot._is_security_update(labels, body)

        assert is_security is True

    def test_cve_in_body_detection(self, bot):
        """Test detection via CVE mention in body."""
        labels = []
        body = "This update fixes CVE-2024-1234"

        is_security = bot._is_security_update(labels, body)

        assert is_security is True

    def test_vulnerability_keyword_detection(self, bot):
        """Test detection via vulnerability keyword."""
        labels = []
        body = "This release addresses a critical vulnerability"

        is_security = bot._is_security_update(labels, body)

        assert is_security is True

    def test_no_security_indicators(self, bot):
        """Test non-security update."""
        labels = [{"name": "dependencies"}]
        body = "Regular dependency update"

        is_security = bot._is_security_update(labels, body)

        assert is_security is False


class TestDependencyPRDetection:
    """Test detection of dependency PRs."""

    @patch('src.agent.LLMDependencyBot._make_request')
    def test_dependabot_pr_detection(self, mock_request, bot):
        """Test detection of Dependabot PR."""
        mock_request.return_value.json.return_value = {
            "user": {"login": "dependabot[bot]"},
            "title": "Bump axios from 1.0.0 to 1.1.0",
            "labels": [{"name": "dependencies"}]
        }

        is_dep_pr = bot.is_dependency_pr(123)

        assert is_dep_pr is True

    @patch('src.agent.LLMDependencyBot._make_request')
    def test_renovate_pr_detection(self, mock_request, bot):
        """Test detection of Renovate PR."""
        mock_request.return_value.json.return_value = {
            "user": {"login": "renovate[bot]"},
            "title": "Update axios to 1.1.0",
            "labels": []
        }

        is_dep_pr = bot.is_dependency_pr(123)

        assert is_dep_pr is True

    @patch('src.agent.LLMDependencyBot._make_request')
    def test_non_dependency_pr(self, mock_request, bot):
        """Test non-dependency PR."""
        mock_request.return_value.json.return_value = {
            "user": {"login": "human-developer"},
            "title": "Add new feature",
            "labels": []
        }

        is_dep_pr = bot.is_dependency_pr(123)

        assert is_dep_pr is False


class TestFallbackDecision:
    """Test fallback decision logic when LLM parsing fails."""

    def test_fallback_ci_failure(self, bot, sample_pr_context):
        """Test fallback blocks on CI failure."""
        sample_pr_context.ci_status = "failure"

        decision, risk, reasoning = bot._fallback_decision(sample_pr_context, "error")

        assert decision == MergeDecision.DO_NOT_MERGE
        assert risk == RiskLevel.CRITICAL

    def test_fallback_major_update(self, bot, sample_pr_context):
        """Test fallback requires approval for major updates."""
        sample_pr_context.update_type = "major"

        decision, risk, reasoning = bot._fallback_decision(sample_pr_context, "error")

        assert decision == MergeDecision.REQUIRE_APPROVAL
        assert risk == RiskLevel.HIGH

    def test_fallback_security_update(self, bot, sample_pr_context):
        """Test fallback auto-merges security updates."""
        sample_pr_context.is_security_update = True

        decision, risk, reasoning = bot._fallback_decision(sample_pr_context, "error")

        assert decision == MergeDecision.AUTO_MERGE
        assert risk == RiskLevel.LOW

    def test_fallback_patch_update(self, bot, sample_pr_context):
        """Test fallback auto-merges patch updates."""
        sample_pr_context.update_type = "patch"

        decision, risk, reasoning = bot._fallback_decision(sample_pr_context, "error")

        assert decision == MergeDecision.AUTO_MERGE
        assert risk == RiskLevel.LOW


class TestToolDefinitions:
    """Test tool definitions for Claude."""

    def test_tools_are_defined(self, bot):
        """Test that tools are properly defined."""
        tools = bot._get_tools_definition()

        assert len(tools) == 3
        tool_names = [tool["name"] for tool in tools]
        assert "fetch_release_notes" in tool_names
        assert "check_cve_database" in tool_names
        assert "analyze_diff" in tool_names

    def test_tool_schemas_valid(self, bot):
        """Test that tool schemas are valid."""
        tools = bot._get_tools_definition()

        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "type" in tool["input_schema"]
            assert "properties" in tool["input_schema"]
            assert "required" in tool["input_schema"]


class TestCIStatus:
    """Test CI status parsing."""

    @patch('src.agent.LLMDependencyBot._make_request')
    def test_all_checks_passing(self, mock_request, bot):
        """Test CI status when all checks pass."""
        mock_request.return_value.json.return_value = {
            "check_runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "completed", "conclusion": "success"}
            ]
        }

        status, conclusion = bot._get_ci_status(123, "abc123")

        assert status == "success"
        assert conclusion == "success"

    @patch('src.agent.LLMDependencyBot._make_request')
    def test_checks_failing(self, mock_request, bot):
        """Test CI status when checks fail."""
        mock_request.return_value.json.return_value = {
            "check_runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "completed", "conclusion": "failure"}
            ]
        }

        status, conclusion = bot._get_ci_status(123, "abc123")

        assert status == "failure"
        assert conclusion == "failure"

    @patch('src.agent.LLMDependencyBot._make_request')
    def test_checks_pending(self, mock_request, bot):
        """Test CI status when checks are pending."""
        mock_request.return_value.json.return_value = {
            "check_runs": [
                {"status": "in_progress", "conclusion": None},
                {"status": "completed", "conclusion": "success"}
            ]
        }

        status, conclusion = bot._get_ci_status(123, "abc123")

        assert status == "pending"
        assert conclusion is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
