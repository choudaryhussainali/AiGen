"""Supabase email and password authentication."""

from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL

_client = create_client(SUPABASE_URL, SUPABASE_KEY)
