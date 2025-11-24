# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### How to Report

1. **Email**: Send details to [INSERT SECURITY EMAIL]
2. **Subject**: `[SECURITY] Brief description`
3. **Include**:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Regular Updates**: Every week until resolved
- **Public Disclosure**: After fix is released (coordinated disclosure)

## Security Considerations

### API Keys

**CRITICAL**: Never commit API keys to the repository!

- ✅ **DO**: Store keys in GitHub Secrets
- ❌ **DON'T**: Hard-code keys in source code
- ❌ **DON'T**: Commit `.env` files
- ❌ **DON'T**: Include keys in logs

### Permissions

The bot requires these GitHub permissions:

```yaml
permissions:
  contents: write       # To merge PRs
  pull-requests: write  # To comment and label
  checks: read          # To read CI status
```

**Why these permissions?**

- `contents: write` - Needed to merge approved PRs
- `pull-requests: write` - Needed to add explanatory comments
- `checks: read` - Needed to verify CI passed

**Security measures:**

- Bot only acts on dependency PRs from known bots (Dependabot, Renovate)
- All actions are logged and transparent
- Human override always available
- Conservative default behavior

### Anthropic API

**Data sent to Anthropic:**

The bot sends the following to Claude API:
- PR title and description
- Dependency name and version
- CI status
- File names changed (not file contents, unless explicitly requested via tool)

**Data NOT sent:**

- Source code (unless `analyze_diff` tool is used)
- Secrets or environment variables
- Private repository information beyond the PR

**Anthropic's data policy:**

- [Anthropic Commercial Terms](https://www.anthropic.com/legal/commercial-terms)
- API requests are not used to train models
- Data is encrypted in transit

### GitHub API

**Tokens:**

- Use `GITHUB_TOKEN` (automatically provided by GitHub Actions)
- Token is scoped to the repository
- Token expires after workflow completes
- Never log token values

**API calls:**

- All GitHub API calls use authenticated requests
- Rate limiting is respected
- Errors are handled gracefully

## Security Best Practices

### For Users

1. **Secrets Management**
   ```yaml
   # ✅ Good
   anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}

   # ❌ Bad
   anthropic-api-key: "sk-ant-api03-..."
   ```

2. **Branch Protection**
   - Require PR reviews for main branch
   - Require status checks to pass
   - Don't allow the bot to bypass these rules

3. **Audit Trail**
   - Review bot decisions in PR comments
   - Check commit messages for reasoning
   - Monitor merged PRs regularly

4. **Testing**
   - Test the bot on a non-production repo first
   - Review auto-merged PRs periodically
   - Adjust configuration based on outcomes

### For Contributors

1. **Code Review**
   - Never merge code that handles secrets unsafely
   - Review all GitHub API permission changes
   - Audit new tool implementations

2. **Dependencies**
   - Keep dependencies updated
   - Review dependency changes carefully
   - Use `pip-audit` or `safety` for Python deps

3. **Testing**
   - Test security-critical changes thoroughly
   - Include tests for permission checks
   - Mock external API calls in tests

## Known Security Considerations

### Auto-Merge Risk

**Risk**: Bot might merge a malicious dependency update

**Mitigations**:
1. Bot only merges if CI passes
2. Conservative decision-making (defaults to human review)
3. All merges include reasoning and are auditable
4. Configurable critical dependencies list
5. Security updates get extra scrutiny

### LLM Decision Risk

**Risk**: Claude might make incorrect decisions

**Mitigations**:
1. Fallback to rule-based logic if LLM fails
2. Transparent reasoning for all decisions
3. Human override always available
4. Conservative system prompt
5. Tool use is limited and sandboxed

### Supply Chain Risk

**Risk**: Compromised dependencies of the bot itself

**Mitigations**:
1. Pin all dependencies
2. Use Dependabot for bot dependencies
3. Review all dependency updates
4. Regular security audits
5. Minimal dependency footprint

## Incident Response

If a security issue is discovered:

1. **Immediate Actions**
   - Assess severity and impact
   - Patch if possible
   - Notify affected users

2. **Communication**
   - Security advisory on GitHub
   - Email to known users
   - Update documentation

3. **Post-Incident**
   - Root cause analysis
   - Improve security measures
   - Update this policy

## Security Checklist

Before using in production:

- [ ] API keys stored in GitHub Secrets
- [ ] Branch protection enabled on main
- [ ] CI/CD pipeline includes security scans
- [ ] Bot tested on non-production repo
- [ ] Team trained on reviewing bot decisions
- [ ] Incident response plan in place
- [ ] Regular security audits scheduled

## Contact

- **Security Issues**: [INSERT SECURITY EMAIL]
- **General Questions**: [INSERT GENERAL EMAIL]
- **GitHub Security Advisory**: Use GitHub's private vulnerability reporting

## Credits

We thank the security research community for helping keep this project secure.

**Responsible Disclosure Hall of Fame:**

_(Names of security researchers who have responsibly disclosed vulnerabilities)_

---

**Thank you for helping keep LLM Dependency Bot secure!**
