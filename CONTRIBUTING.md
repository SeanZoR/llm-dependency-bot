# Contributing to LLM Dependency Bot

Thank you for your interest in contributing! This project aims to demonstrate and advance agentic AI patterns for practical software engineering tasks.

## 🎯 Project Vision

This bot showcases:
- **True agentic AI** - LLM as reasoning engine, not just pattern matching
- **Transparent AI** - Explainable decisions with natural language reasoning
- **Production-ready code** - Clean architecture, comprehensive tests, type safety
- **Educational value** - Teaching modern AI agent patterns

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- GitHub account
- Anthropic API key (for testing)

### Setup Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/llm-dependency-bot.git
cd llm-dependency-bot
```

2. **Create a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements-dev.txt
```

4. **Install pre-commit hooks**

```bash
pre-commit install
```

5. **Set up environment variables**

Create `.env` file (never commit this!):

```bash
GITHUB_TOKEN=your_github_token
ANTHROPIC_API_KEY=your_anthropic_key
GITHUB_REPOSITORY=test-owner/test-repo
```

6. **Run tests**

```bash
pytest
```

## 🔨 Development Workflow

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring
- `test/` - Adding tests

Example: `feature/add-slack-notifications`

### Making Changes

1. **Create a branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

- Write clear, documented code
- Add type hints
- Include docstrings
- Follow existing patterns

3. **Run quality checks**

```bash
# Format code
black src tests

# Lint
ruff check src tests --fix

# Type check
mypy src

# Run tests
pytest --cov=src

# Or run all via pre-commit
pre-commit run --all-files
```

4. **Commit your changes**

```bash
git add .
git commit -m "feat: add slack notification support"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

5. **Push and create PR**

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 📝 Code Style

### Python Style

- **Formatting**: Black (line length: 100)
- **Linting**: Ruff
- **Type hints**: Required for all functions
- **Docstrings**: Google style

Example:

```python
def analyze_dependency(
    dependency: str,
    version: str,
    context: Dict[str, Any]
) -> Tuple[RiskLevel, str]:
    """
    Analyze a dependency update for risk.

    Args:
        dependency: Name of the dependency
        version: Target version
        context: Additional context for analysis

    Returns:
        Tuple of (risk_level, reasoning)

    Raises:
        ValueError: If dependency name is invalid
    """
    # Implementation
    pass
```

### File Organization

```
src/
├── agent.py          # Main agent implementation
├── tools.py          # Tool definitions (future)
└── utils.py          # Utility functions (future)

tests/
├── test_agent.py     # Agent tests
├── test_tools.py     # Tool tests
└── fixtures/         # Test data
```

## 🧪 Testing

### Writing Tests

- **Unit tests**: Test individual functions
- **Integration tests**: Test agent workflow
- **Mocking**: Mock GitHub API and Anthropic API calls

Example test:

```python
def test_security_update_detection(bot):
    """Test that security updates are correctly identified."""
    labels = [{"name": "security"}]
    body = "Fixes CVE-2024-1234"

    is_security = bot._is_security_update(labels, body)

    assert is_security is True
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/test_agent.py::test_security_update_detection

# Verbose output
pytest -v

# Watch mode (requires pytest-watch)
ptw
```

## 📚 Documentation

### Docstrings

All public functions must have docstrings:

```python
def tool_name(param: str) -> str:
    """
    Brief one-line description.

    More detailed description if needed. Explain the purpose,
    important behavior, and usage patterns.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised
    """
```

### Adding Documentation

Documentation lives in `docs/`:

- `ARCHITECTURE.md` - System design
- `TOOL-USE-GUIDE.md` - Creating custom tools
- `PROMPT-ENGINEERING.md` - Customizing AI behavior

## 🎯 What to Contribute

### High-Priority Areas

1. **Tool Implementations**
   - Real release notes fetching (npm, PyPI, RubyGems)
   - CVE database integration (Snyk, GitHub Security)
   - Performance impact analysis
   - Dependency tree analysis

2. **Multi-Agent Features**
   - Specialized agents (security, compatibility, performance)
   - Agent coordination patterns
   - Consensus mechanisms

3. **Learning & Adaptation**
   - Track merge outcomes
   - Learn from failures
   - Adjust decision patterns

4. **Integrations**
   - Slack/Discord notifications
   - Custom webhooks
   - Analytics dashboard

5. **Testing & Quality**
   - Increase test coverage
   - Add integration tests
   - Performance benchmarks

### Good First Issues

Look for issues labeled `good-first-issue`:
- Documentation improvements
- Test additions
- Simple bug fixes
- Type hint additions

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues
2. Update to latest version
3. Try to reproduce with minimal example

### Bug Report Template

```markdown
## Description
Brief description of the bug

## To Reproduce
Steps to reproduce:
1. Configure bot with...
2. Create PR with...
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python version:
- Bot version:
- OS:

## Logs
```
Relevant logs or error messages
```
```

## 💡 Feature Requests

### Proposal Template

```markdown
## Feature Description
Brief description of the feature

## Use Case
Why is this needed? What problem does it solve?

## Proposed Implementation
How might this work?

## Alternatives Considered
Other approaches considered

## Additional Context
Screenshots, examples, references
```

## 🏆 Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes
- README acknowledgments

Significant contributions may earn you:
- Maintainer status
- Your name in the hall of fame
- Swag (if/when we have it!)

## 📋 Pull Request Checklist

Before submitting:

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`black src tests`)
- [ ] Linting passes (`ruff check src tests`)
- [ ] Type checking passes (`mypy src`)
- [ ] Documentation is updated
- [ ] Changelog is updated (for significant changes)
- [ ] Commit messages follow convention
- [ ] PR description explains the change

## 🤝 Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

**Expected behavior:**
- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

**Unacceptable behavior:**
- Harassment or discriminatory language
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information

## 📞 Questions?

- 💬 [GitHub Discussions](https://github.com/yourusername/llm-dependency-bot/discussions)
- 🐛 [Issue Tracker](https://github.com/yourusername/llm-dependency-bot/issues)
- 📧 Email: [maintainer email]

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to LLM Dependency Bot!** 🙏

Every contribution, no matter how small, helps advance the state of agentic AI.
