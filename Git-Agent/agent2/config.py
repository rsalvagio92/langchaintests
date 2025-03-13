import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub Authentication
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_USER = os.getenv("GITHUB_USER")
REPO_PATH = os.getenv("LOCAL_REPO_PATH", "local_repo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants
MAX_CONTENT_DISPLAY = 1000  # Maximum characters to display in logs
MAX_FILE_SIZE = 50000  # Maximum file size to process in tools