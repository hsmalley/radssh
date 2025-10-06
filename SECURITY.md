# Security Policy

## Supported Versions

We provide security updates for the following versions of RadSSH:

| Version | Supported          |
| ------- | ------------------ |
| 2.x.x   | :white_check_mark: |
| 1.x.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in RadSSH, please report it privately to help us address it quickly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by:

1. **Email**: Send details to [hsmalley@example.com](mailto:hsmalley@example.com)
2. **GitHub Security**: Use GitHub's private vulnerability reporting feature at [https://github.com/hsmalley/radssh/security](https://github.com/hsmalley/radssh/security)

### What to Include

Please include as much of the following information as possible:

- Type of vulnerability (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source files related to the manifestation of the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Acknowledgment**: We aim to acknowledge receipt of vulnerability reports within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Updates**: We will provide regular updates on our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### Security Best Practices

When using RadSSH:

1. **Keep Updated**: Always use the latest supported version
2. **Secure Credentials**: Use strong authentication methods (keys over passwords)
3. **Network Security**: Use RadSSH only on trusted networks when possible
4. **Audit Logs**: Monitor and audit SSH connections and commands
5. **Principle of Least Privilege**: Grant minimal necessary permissions

### Disclosure Policy

- We will work with you to understand and resolve the issue
- We will not pursue legal action against researchers who report vulnerabilities in good faith
- We may publicly acknowledge your responsible disclosure (with your permission)
- We will coordinate public disclosure timing to ensure users have time to update

## Security Features

RadSSH includes several security features:

- **SSH Key Authentication**: Support for SSH key-based authentication
- **Connection Encryption**: All connections use SSH encryption
- **Plugin Sandboxing**: Plugin system with controlled execution environment
- **Audit Logging**: Comprehensive logging of commands and connections

Thank you for helping to keep RadSSH secure!