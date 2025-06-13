import os
import json
from google.oauth2.service_account import Credentials

SHEET_ID = os.getenv("SHEET_ID")

def get_credentials():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])

    # Fixa radbrytningar i private_key
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    return Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
