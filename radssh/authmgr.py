"""
Simplified AuthManager for Mitogen integration.

This module provides a basic AuthManager that holds user credentials.
Mitogen handles the actual authentication mechanisms.
"""

import os
import warnings
import logging

class AuthManager(object):
    """Manage credentials for Mitogen connections."""

    def __init__(
        self,
        default_user,
        auth_file=None,
        default_password=None,
        **kwargs # Absorb other params for compatibility
    ):
        self.logger = logging.getLogger("radssh.auth")
        if default_user:
            self.default_user = default_user
        else:
            self.default_user = os.environ.get("SSH_USER", os.environ.get("USER"))
        
        self.default_password = default_password

        if auth_file:
            self.logger.warning(f"Auth file ({auth_file}) is not supported with the Mitogen backend.")

    def __str__(self):
        return f"<AuthManager for {self.default_user}>"