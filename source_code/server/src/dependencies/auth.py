"""Compatibility imports; new code uses src.middlewares.auth."""
from src.middlewares.auth import (
    bearer_scheme, get_token_payload, get_current_user, require_roles,
)
