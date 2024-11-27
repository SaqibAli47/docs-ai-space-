import os
import json
import dotenv

dotenv.load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY", "")

MICROSOFT_AUTHORITY = os.getenv("MICROSOFT_AUTHORITY", "https://login.microsoftonline.com/common")
MICROSOFT_SCOPE = os.getenv("MICROSOFT_SCOPE", "User.Read").split(",")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost/api/microsoft/callback/")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BUILD_PATH = os.getenv("BUILD_PATH", "front/build")
ALLOWED_TENANTS = os.getenv("ALLOWED_TENANTS", "").split(",")

AZURE_AI_SEARCH_KEY = os.getenv("AZURE_AI_SEARCH_KEY", "")
AZURE_AI_SEARCH_INDEX = os.getenv("AZURE_AI_SEARCH_INDEX", "")
AZURE_AI_SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT", "")

OPENAI_API_TYPE = os.getenv("OPENAI_API_TYPE", "azure")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2023-05-15")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-35-turbo-16k")
OPENAI_API_MAX_TOKENS = int(os.getenv("OPENAI_API_MAX_TOKENS", 1000))
OPENAI_API_TEMPERATURE = float(os.getenv("OPENAI_API_TEMPERATURE", 0.1))
OPENAI_API_TOP_P = float(os.getenv("OPENAI_API_TOP_P", 0.9))
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
NO_OF_CONTEXT=int(os.getenv("NO_OF_CONTEXT", 5))
BATCH_SIZE=int(os.getenv("BATCH_SIZE", 10))

DEFAULT_USER = os.getenv("DEFAULT_USER", "")
USER_PASSWORD = os.getenv("USER_PASSWORD", "")

SQL_SERVER = os.getenv("SQL_SERVER", "")
SQL_DATABASE = os.getenv("SQL_DATABASE", "")
SQL_UID = os.getenv("SQL_UID", "")
SQL_PWD = os.getenv("SQL_PWD", "")
OPENAI_RESOURCES = [
    {
        'apiKey': os.getenv("OPENAI_API_KEY_DEV", ""),
        'baseURL': ''
    },
    {
        'apiKey': os.getenv("OPENAI_API_KEY_PROD_1", ""),
        'baseURL': ''
    },
    {
        'apiKey': os.getenv("OPENAI_API_KEY_PROD_2", ""),
        'baseURL': ''
    },
    {
        'apiKey': os.getenv("OPENAI_API_KEY_PROD_3", ""),
        'baseURL': ''
    }
]