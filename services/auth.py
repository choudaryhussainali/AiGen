"""Supabase email and password authentication."""

from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL

_client = create_client(SUPABASE_URL, SUPABASE_KEY)


def _friendly_error(error):
    """Supabase messages are developer facing, so map them to plain English."""
    text = str(error).lower()
    if "already registered" in text or "already exists" in text:
        return "Email already registered."
    if "invalid login" in text or "invalid credentials" in text:
        return "Invalid email or password."
    if "password" in text and "6" in text:
        return "Password must be at least 6 characters."
    if "email" in text and "valid" in text:
        return "Please enter a valid email address."
    return "Something went wrong. Please try again."
