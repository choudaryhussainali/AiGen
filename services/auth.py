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
    if "not confirmed" in text:
        return "Please confirm your email address before logging in."
    if "rate limit" in text:
        return "Too many attempts. Please wait a minute and try again."
    if "password" in text and "6" in text:
        return "Password must be at least 6 characters."
    if "email" in text and "valid" in text:
        return "Please enter a valid email address."
    return "Something went wrong. Please try again."


def sign_up(email, password, first_name, last_name):
    # Names live in the Supabase user metadata, so no table of our own is needed.
    names = {"first_name": first_name, "last_name": last_name}
    try:
        result = _client.auth.sign_up(
            {"email": email, "password": password, "options": {"data": names}}
        )
    except Exception as error:
        raise ValueError(_friendly_error(error))
    if result.user is None:
        raise ValueError("Could not create that account.")


def sign_in(email, password):
    try:
        result = _client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception as error:
        raise ValueError(_friendly_error(error))
    if result.session is None:
        raise ValueError("Invalid email or password.")
    return {
        "email": result.user.email,
        "access_token": result.session.access_token,
    }


def sign_out():
    # The anon key cannot revoke another user's token, so logout is local:
    # the RAM session is wiped and the cookie is cleared by the route.
    try:
        _client.auth.sign_out()
    except Exception:
        pass
