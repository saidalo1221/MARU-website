"""Password strength rules (PRD ТЗ№3 §56, §58).

Customers: at least 8 characters with a letter and a digit, not a well-known
weak password and not the account's own email. Admin roles get the strong
policy: at least 12 characters with upper and lower case, a digit and a symbol.
"""

import re
from typing import Optional

MAX_LENGTH = 128  # keeps hashing cost bounded

_COMMON = {
    "password", "password1", "password123", "12345678", "123456789", "1234567890", "qwertyui",
    "qwerty123", "iloveyou", "11111111", "00000000", "abc12345", "admin123", "letmein1",
}


class PasswordPolicyError(ValueError):
    """The message is safe to show to the user."""


def validate_password(password: str, email: Optional[str] = None, strong: bool = False) -> None:
    if len(password) > MAX_LENGTH:
        raise PasswordPolicyError(f"Password must be at most {MAX_LENGTH} characters")
    minimum = 12 if strong else 8
    if len(password) < minimum:
        raise PasswordPolicyError(f"Password must be at least {minimum} characters")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise PasswordPolicyError("Password must contain at least one letter and one digit")
    if password.lower() in _COMMON:
        raise PasswordPolicyError("That password is too common")
    if email and password.lower() == email.lower():
        raise PasswordPolicyError("Password must not be your email address")
    if strong and not (re.search(r"[a-z]", password) and re.search(r"[A-Z]", password) and re.search(r"[^A-Za-z0-9]", password)):
        raise PasswordPolicyError("Admin passwords need upper and lower case letters and a symbol")
