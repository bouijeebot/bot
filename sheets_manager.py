import gspread
from google.oauth2.service_account import Credentials

GOOGLE_CREDENTIALS_FILE = "credentials.json"
SHEET_ID = "1OdUvncaZUtf8z6ZfzOS0RYNJ3BBIv6wJPynBjRXeGWs"  # <-- Ersätt denna!

def get_worksheet(sheet_name):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SHEET_ID)
    return sh.worksheet(sheet_name)