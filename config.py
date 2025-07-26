import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
FILTERS_FILE = "filters.json"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBAPP_PORT = int(os.getenv("PORT", 10000))
