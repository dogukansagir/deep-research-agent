from dotenv import load_dotenv
import os
load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TAVILY_API_KEY= os.getenv("TAVILY_API_KEY")
LANGFUSE_PUBLIC_KEY= os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY= os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST="https://cloud.langfuse.com"
OPENALEX_URL = "https://api.openalex.org/works"

if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is not set")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set")
if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
    raise ValueError("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set")