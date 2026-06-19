# Security Policy

## Supported Versions

We take security seriously and release patches for security vulnerabilities. Here are the versions currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We appreciate your efforts to responsibly disclose your findings. Please follow these guidelines:

### 📧 Contact Information

- **Email**: [security@example.com](mailto:security@example.com)
- **GitHub Security Advisories**: Use the [Security tab](https://github.com/YOUR_USERNAME/screenshot-analytics-mvp/security/advisories) in this repository

### 🔒 What to Include

When reporting a vulnerability, please provide:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** assessment
4. **Suggested fix** (if you have one)
5. **Your contact information** for follow-up questions

### ⏱️ Response Timeline

- **Initial Response**: Within 48 hours
- **Vulnerability Assessment**: Within 5 business days
- **Patch Development**: Within 14 business days (depending on severity)
- **Public Disclosure**: Coordinated with reporter after patch release

### 🛡️ Security Best Practices

#### For Users

1. **Environment Variables**:
   - Never commit `.env` files to version control
   - Use strong, unique passwords for database and admin accounts
   - Rotate credentials regularly

2. **Docker Security**:
   - Keep Docker and dependencies updated
   - Run containers with minimal privileges
   - Use read-only mounts where possible

3. **Network Security**:
   - Enable firewall rules for port 8501 (dashboard)
   - Use HTTPS in production deployments
   - Restrict database access to internal network only

4. **Google Service Account**:
   - Store credentials securely (`config/service_account.json`)
   - Limit service account permissions to minimum required
   - Rotate keys periodically

#### For Contributors

1. **Code Security**:
   - Follow secure coding practices
   - Validate all user inputs
   - Use parameterized queries for database operations
   - Avoid hardcoded secrets or credentials

2. **Dependencies**:
   - Regularly update Python packages
   - Monitor for known vulnerabilities using `pip-audit` or `safety`
   - Pin dependency versions in requirements.txt

3. **Testing**:
   - Include security tests when adding new features
   - Test for common vulnerabilities (SQL injection, XSS, etc.)
   - Run static analysis tools (bandit, flake8)

### 🚨 Known Security Considerations

1. **Screenshot Privacy**: 
   - Screenshots may contain sensitive information
   - Implement appropriate access controls
   - Consider data encryption at rest

2. **OCR Processing**:
   - OCR text is stored in database
   - Ensure database backups are encrypted
   - Implement proper data retention policies

3. **Dashboard Access**:
   - Default admin credentials should be changed immediately
   - Implement IP whitelisting for production
   - Enable audit logging

### 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Python Security Guide](https://docs.python.org/3/library/security_warnings.html)

---

**Thank you for helping keep this project secure!** 🔐
