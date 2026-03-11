"""Settings aus .env laden."""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "")
VAPI_BASE_URL = "https://api.vapi.ai"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not VAPI_API_KEY:
    raise ValueError("VAPI_API_KEY nicht gesetzt. Bitte .env prüfen.")

if not VAPI_ASSISTANT_ID:
    raise ValueError("VAPI_ASSISTANT_ID nicht gesetzt. Bitte .env prüfen.")
